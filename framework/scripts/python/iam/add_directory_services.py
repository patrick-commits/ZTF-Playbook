from typing import Dict
from framework.helpers.log_utils import get_logger
from framework.scripts.python.helpers.v4.iam.directory_services import DirectoryServices
from framework.scripts.python.script import Script
from framework.helpers.helper_functions import read_creds

logger = get_logger(__name__)


class AddDirectoryServices(Script):
    """
    Class that adds DirectoryService in Objects
    """
    def __init__(self, data: Dict, **kwargs):
        self.data = data
        self.v4_api_util = self.data["v4_api_util"]
        self.ad_configs = self.data.get("oss_directory_services", []) or self.data.get("objects", {}). \
            get("directory_services", [])
        super(AddDirectoryServices, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            directory_services_obj = DirectoryServices(self.v4_api_util)
            if self.ad_configs:
                for ad_config in self.ad_configs:

                    if directory_services_obj.get_by_domain_name(ad_config.get("ad_domain")):
                        self.logger.warning(f"SKIP: Directory with domain {ad_config['ad_domain']} is "
                                            f"already present in {self.data['pc_ip']!r}")
                        continue

                    if "service_account_credential" not in ad_config:
                        self.exceptions.append(f"service_account_credential is missing in the payload for "
                                               f"{ad_config['ad_name']}")
                        continue

                    service_account_credential = ad_config.pop("service_account_credential")
                    # get credentials from the payload
                    try:
                        ad_config["service_account_username"], ad_config["service_account_password"] = (
                            read_creds(data=self.data, credential=service_account_credential))
                    except Exception as e:
                        self.exceptions.append(e)
                        return
                    response = directory_services_obj.add_directory_service(
                        name=ad_config["ad_name"],
                        domain_name=ad_config["ad_domain"],
                        url=ad_config["ad_directory_url"],
                        service_account_username=ad_config["service_account_username"],
                        service_account_password=ad_config["service_account_password"]
                    )
                    logger.debug(response)
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        if not self.ad_configs:
            return

        self.results["AddDirectoryServices"] = {}
        for ad_config in self.ad_configs:
            # Initial status
            self.results["AddDirectoryServices"][ad_config["ad_name"]] = "CAN'T VERIFY"

            directory_services_obj = DirectoryServices(self.v4_api_util)

            try:
                if directory_services_obj.get_by_domain_name(ad_config.get("ad_domain")):
                    self.results["AddDirectoryServices"][ad_config["ad_name"]] = "PASS"
                else:
                    self.results["AddDirectoryServices"][ad_config["ad_name"]] = "FAIL"
            except Exception as e:
                self.logger.debug(e)
                self.logger.info(f"Exception occurred during the verification of {type(self).__name__!r}")