from typing import Dict
from framework.helpers.log_utils import get_logger
from framework.scripts.python.helpers.v4.iam.user_groups import UserGroups
from framework.scripts.python.helpers.v4.iam.directory_services import DirectoryServices
from framework.scripts.python.script import Script

logger = get_logger(__name__)


class AddUserGroups(Script):
    """
    Class that adds User Groups to PC
    """
    def __init__(self, data: Dict, **kwargs):
        self.data = data
        self.v4_api_util = self.data["v4_api_util"]
        self.user_groups = self.data.get("user_groups")
        super(AddUserGroups, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            user_group_obj = UserGroups(self.v4_api_util)
            directory_services_obj = DirectoryServices(self.v4_api_util)

            if self.user_groups:
                for user_group in self.user_groups:
                    if user_group_obj.get_by_name_and_type(user_group.get("name"),user_group.get("group_type")):
                        self.logger.warning(f"SKIP: User Group of Type {user_group['group_type']} with name {user_group['name']} is "
                                            f"already present in {self.data['pc_ip']!r}")
                        continue
                    else:
                        idp_uuid = directory_services_obj.get_uuid_by_directory_service_name(user_group.get("idp"))
                        if not idp_uuid:
                            self.exceptions.append(f"IDP with name {user_group.get('idp')} not found")
                            continue
                        distinguished_name = directory_services_obj.get_distinguished_name_user_group(
                            directory_service_uuid = idp_uuid,
                            name = user_group.get("name")
                        )

                        if not distinguished_name:
                            self.exceptions.append(f"User Group with name {user_group.get('name')} not found in IDP {user_group.get('idp')}")
                            continue

                        response = user_group_obj.add_user_group(
                            group_type=user_group["group_type"],
                            name=user_group["name"],
                            idp_id=idp_uuid,
                            distinguished_name=distinguished_name
                        )

                        logger.debug(response)
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        if not self.user_groups:
            return


        self.results["AddUserGroups"] = {}

        user_group_obj = UserGroups(self.v4_api_util)

        try:
            user_groups = user_group_obj.list_user_groups()
            imported_user_groups = set([(ug.get("name"),ug.get("group_type")) for ug in user_groups["data"]])
            for user_group in self.user_groups:
                self.results["AddUserGroups"][user_group["name"]] = "CAN'T VERIFY"
                if (user_group["name"].lower(), user_group["group_type"]) in imported_user_groups:
                    self.results["AddUserGroups"][user_group["name"]] = "PASS"
                else:
                    self.results["AddUserGroups"][user_group["name"]] = "FAIL"
        except Exception as e:
            self.logger.debug(e)
            self.logger.info(f"Exception occurred during the verification of {type(self).__name__!r}")