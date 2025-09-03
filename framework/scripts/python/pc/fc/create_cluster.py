import time
import json
from framework.helpers.log_utils import get_logger
from framework.scripts.python.script import Script
from framework.scripts.python.helpers.fc.image_cluster_script import ImageClusterScript
from framework.scripts.python.helpers.batch_script import BatchScript
from framework.scripts.python.helpers.fc.imaged_nodes import ImagedNode
from framework.scripts.python.helpers.fc.monitor_fc_deployment import MonitorDeployment
from framework.scripts.python.helpers.fc.update_fc_heartbeat_interval import UpdateFCHeartbeatInterval
from framework.helpers.helper_functions import read_creds
from framework.helpers.general_utils import get_ip_and_create_host_record, assign_ips_from_ipam, update_network_info_in_existing_node_dict

logger = get_logger(__name__)

class CreateCluster(Script):
    """
    Class to Create a cluster using Foundation Central.
    """

    def __init__(self, **data):
        self.data = data["data"]
        self.pc_session = self.data["pc_session"]
        self.cvm_username, self.cvm_password = read_creds(data=self.data, credential=self.data["cvm_credential"])
        self.ipam_obj = self.data.get("ipam_session")
        super(CreateCluster, self).__init__()
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        """
        Execute the FC Create Cluster Script.
        """
        try:
            self.logger.info("Executing FC Create Cluster ...")
            overall_result = {}

            create_cluster_op = BatchScript(parallel=True)

            # Get the FC operations for the clusters
            imaged_node_obj = ImagedNode(session=self.pc_session)
            
            if self.data.get("create_clusters"):
                self.logger.info("Deploying Clusters in Foundation Central...")
                for cluster in self.data["create_clusters"]:
                    nodes_list = cluster.get("nodes_list", [])
                    node_serial_list = [node["node_serial"] for node in nodes_list]
                    existing_node_detail_dict = imaged_node_obj.node_details_by_node_serial(
                        node_serial_list
                        )

                    cluster_data = {
                            "cluster_name": cluster["cluster_name"],
                            "nodes_list": list(existing_node_detail_dict.values()),
                            "skip_cluster_creation" : False
                        }
                    if cluster.get("common_network_settings"):
                        cluster_data["common_network_settings"] = cluster["common_network_settings"]

                    cluster_data["cluster_size"] = len(nodes_list)

                    if len(existing_node_detail_dict) < cluster_data["cluster_size"]:
                        self.logger.error(f"Not enough available nodes for cluster deployment {cluster['cluster_name']}")
                        self.exceptions.append(f"Not enough available nodes for cluster deployment {cluster['cluster_name']}")
                        continue
                    
                    cluster_data["nodes_list"] = list(existing_node_detail_dict.values())

                    if not self.ipam_obj:
                        if not cluster.get("cluster_external_ip"):
                            cluster_name = cluster.get('cluster_name', 'Unknown Cluster')
                            self.logger.warning(f"Cluster External IP not provided. Proceeding without Cluster VIP "
                                f"for cluster {cluster_name}")
                    else:
                        cluster_vip, cluster_vip_error = get_ip_and_create_host_record(
                            ipam_obj = self.ipam_obj, logger_obj = self.logger,
                            fqdn=f"{cluster['cluster_name']}.{self.data['ipam_config']['domain']}",
                            subnet=self.data["ipam_config"].get("host_subnet"),
                            ip=cluster.get("cluster_external_ip"))

                        if cluster_vip_error:
                            self.exceptions.append(cluster_vip_error)
                        else:
                            cluster["cluster_external_ip"] = cluster_vip
                            cluster_data["cluster_external_ip"] = cluster_vip
                    
                    # If the cluster is a single node, check if one node cluster is supported
                    if len(cluster_data["nodes_list"]) == 1:
                        if not existing_node_detail_dict[nodes_list[0]["node_serial"]]["hardware_attributes"].get("one_node_cluster"):
                            self.logger.error(f"One Node Cluster is not enabled in the Node for the cluster {cluster['cluster_name']}.")
                            self.exceptions.append(f"One Node Cluster is not enabled in the Node for the cluster {cluster['cluster_name']}.")
                            continue
                    
                    # If the cluster is a two node cluster, check if two node cluster is supported
                    if len(cluster_data["nodes_list"]) == 2:
                        if not existing_node_detail_dict[nodes_list[0]["node_serial"]].get("hardware_attributes", {}).get("two_node_cluster") and \
                           not existing_node_detail_dict[nodes_list[1]["node_serial"]].get("hardware_attributes", {}).get("two_node_cluster"):
                            self.logger.error(f"Two Node Cluster is not enabled in either of the Nodes for the cluster {cluster['cluster_name']}.")
                            self.exceptions.append(f"Two Node Cluster is not enabled in either of the Nodes for the cluster {cluster['cluster_name']}.")
                            continue

                    for node in nodes_list:
                        for key, value in node.items():
                            if key != "node_serial":
                                existing_node_detail_dict[node["node_serial"]][key] = value
                        if cluster.get("network"):
                            update_network_info_in_existing_node_dict(
                                node["node_serial"], existing_node_detail_dict, cluster["network"])
                        if self.ipam_obj:
                            success, error_message = assign_ips_from_ipam(
                                node_info=existing_node_detail_dict[node["node_serial"]], ipam_config=self.data["ipam_config"],
                                ipam_obj=self.ipam_obj, logger_obj=self.logger
                            )
                            if not success:
                                self.logger.error(f"Failed to assign IPs from IPAM for node {node['node_serial']}: {error_message}")
                                self.exceptions.append(error_message)
                                break # Skip the cluster deployment if IP assignment fails
                    
                    # Add the FC deployment operation to the batch script
                    create_cluster_op.add(ImageClusterScript(
                            pc_session=self.pc_session, cluster_data=cluster_data,
                            fc_deployment_logger=self.logger))
                
                # Run the deployments
                cluster_uuid_dict = create_cluster_op.run()

                # Creating Batch script to monitor all the FC deployments
                monitor_deployment_script = BatchScript(parallel=True, max_workers=40)

                if cluster_uuid_dict:
                    for cluster_name, imaged_cluster_uuid in cluster_uuid_dict.items():
                        monitor_deployment_script.add(MonitorDeployment(pc_session=self.pc_session, cluster_name=cluster_name,
                                                                        imaged_cluster_uuid=imaged_cluster_uuid,
                                                                        fc_deployment_logger=self.logger))

                    self.logger.info(f"Wait for 15 minutes to monitor deployment status for all clusters")
                    time.sleep(15 * 60)
                    deployment_result = monitor_deployment_script.run()
                    overall_result.update(deployment_result)

        except Exception as e:
            self.logger.error("Exception occurred during FC Create Cluster execution")
            self.exceptions.append(e)
        finally:
            self.logger.info(json.dumps(overall_result, indent=2))
            self.data["json_output"] = overall_result

    def verify(self, **kwargs):
        pass