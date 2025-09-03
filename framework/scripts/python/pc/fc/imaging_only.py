import time
from framework.helpers.log_utils import get_logger
from framework.scripts.python.script import Script
from framework.scripts.python.helpers.fc.image_cluster_script import ImageClusterScript
from framework.scripts.python.helpers.batch_script import BatchScript
from framework.scripts.python.helpers.fc.imaged_nodes import ImagedNode
from framework.scripts.python.helpers.fc.monitor_fc_deployment import MonitorDeployment
from framework.helpers.helper_functions import read_creds
from framework.helpers.general_utils import update_network_info_in_existing_node_dict, assign_ips_from_ipam

logger = get_logger(__name__)

class Imaging(Script):
    """
    Class to Image Nodes using Foundation Central (FC)
    """

    def __init__(self, **data):
        self.data = data["data"]
        self.pc_session = self.data["pc_session"]
        self.cvm_username, self.cvm_password = read_creds(data=self.data, credential=self.data["cvm_credential"])
        self.ipam_obj = self.data.get("ipam_session")
        super(Imaging, self).__init__()
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        """
        Execute Imaging in Foundation Central (FC)
        """
        try:
            self.logger.info("Executing Imaging Script...")
            overall_result = {}

            imaging_op = BatchScript(parallel=True)

            # Get the FC operations for the clusters
            imaged_node_obj = ImagedNode(session=self.pc_session)
            
            if self.data.get("imaging"):
                self.logger.info("Imaging Nodes in Foundation Central...")
                for batch in self.data["imaging"]:
                    if len(batch["nodes_list"]) == 1:
                        self.logger.error(
                            f"FC does not support imaging a single node cluster. "
                            f"Skipping deployment for cluster with nodes: {batch['nodes_list']}")
                        self.exceptions.append(
                            "FC does not support imaging a single node cluster. "
                            "Skipping deployment for cluster")
                        continue

                    node_list = batch["nodes_list"]
                    imaging_node_serial_list = [node["node_serial"] for node in node_list]

                    # Get Existing node details from FC for node serials given in the cluster
                    existing_node_detail_dict = imaged_node_obj.node_details_by_node_serial(imaging_node_serial_list)

                    if len(existing_node_detail_dict) < len(imaging_node_serial_list):
                        #If the given Node serials are not available in FC, skip the Imaging
                        self.logger.error(
                            f"Few of Node serials {imaging_node_serial_list} not available in FC. "
                            f"Skipping Imaging for these nodes")
                        self.exceptions.append(
                            f"Few of Node serials {imaging_node_serial_list} not available in FC. "
                            f"Skipping Imaging for these nodes")
                        continue

                    for node in node_list:
                        node_serial = node["node_serial"]
                        for key, value in node.items():
                            existing_node_detail_dict[node_serial][key] = value

                        if batch.get("network"):
                            update_network_info_in_existing_node_dict(
                                node_serial, existing_node_detail_dict, batch["network"]
                                )

                        # Assign IPs from IPAM if IPAM object is provided
                        if self.ipam_obj:
                            success, error_message = assign_ips_from_ipam(
                                node_info=existing_node_detail_dict[node_serial], ipam_config=self.data["ipam_config"],
                                ipam_obj=self.ipam_obj, logger_obj=self.logger
                            )
                            if not success:
                                self.logger.error(f"Failed to assign IPs from IPAM for node {node['node_serial']}: {error_message}")
                                self.exceptions.append(error_message)
                                break

                        existing_node_detail_dict[node_serial]["image_now"] = True # Set image_now to True in Payload for FC Imaging

                    imaging_data = {
                        "nodes_list": list(existing_node_detail_dict.values()),
                        "aos_package_url": batch["imaging_parameters"]["aos_package_url"],
                        "hypervisor_isos": batch["hypervisor_isos"],
                        "common_network_settings": batch.get("common_network_settings"),
                        "skip_cluster_creation" : True
                    }

                    if batch["imaging_parameters"].get("aos_package_sha256sum"):
                        imaging_data["aos_package_sha256sum"] = batch["imaging_parameters"]["aos_package_sha256sum"]
                    if batch["imaging_parameters"].get("aos_metadata_url"):
                        imaging_data["aos_metadata_url"] = batch["imaging_parameters"]["aos_metadata_url"]

                    # Add the FC deployment operation to the batch script
                    imaging_op.add(ImageClusterScript(
                        pc_session=self.pc_session, cluster_data=imaging_data,
                        fc_deployment_logger=self.logger))
                # Run the deployments
                imaging_uuid_dict = imaging_op.run()

                # Creating Batch script to monitor all the FC deployments
                monitor_deployment_script = BatchScript(parallel=True, max_workers=40)

                if imaging_uuid_dict:
                    for cluster_name, imaged_cluster_uuid in imaging_uuid_dict.items():
                        monitor_deployment_script.add(MonitorDeployment(
                            pc_session=self.pc_session, cluster_name=cluster_name,
                            imaged_cluster_uuid=imaged_cluster_uuid,
                            fc_deployment_logger=self.logger))

                    self.logger.info(f"Wait for 15 minutes to monitor deployment status for Imaging Nodes")
                    time.sleep(15 * 60)
                    deployment_result = monitor_deployment_script.run()
                    overall_result.update(deployment_result)

        except Exception as e:
            self.logger.error(f"Exception occurred during Imaging execution: {e}", exc_info=True)
            self.exceptions.append(e)

    def verify(self, **kwargs):
        pass