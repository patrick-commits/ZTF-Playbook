from typing import Dict
from framework.helpers.log_utils import get_logger
from framework.scripts.python.helpers.v4.iam.users import Users
from framework.scripts.python.helpers.v4.iam.directory_services import DirectoryServices
from framework.scripts.python.script import Script

logger = get_logger(__name__)


class ImportUsers(Script):
    """
    Class that imports Users to PC
    """
    def __init__(self, data: Dict, **kwargs):
        self.data = data
        self.v4_api_util = self.data["v4_api_util"]
        self.users = self.data.get("users") or self.data.get("directory_services", {}).get("users")
        super(ImportUsers, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            users_obj = Users(self.v4_api_util)
            directory_services_obj = DirectoryServices(self.v4_api_util)

            if self.users:
                for user in self.users:
                    if users_obj.get_by_username_and_type(user.get("username"), user.get("user_type")):
                        self.logger.warning(f"SKIP: User of Type {user['user_type']} with username {user['username']} is "
                                            f"already present in {self.data['pc_ip']!r}")
                        continue
                    else:
                        idp_uuid = directory_services_obj.get_uuid_by_directory_service_name(user.get("idp"))
                        if not idp_uuid:
                            self.exceptions.append(f"IDP with name {user.get('idp')} not found")
                            continue

                        response = users_obj.import_user(
                            user_type=user["user_type"],
                            username=user["username"],
                            idp_uuid=idp_uuid,
                        )

                        logger.debug(response)
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        if not self.users:
            return

        self.results["ImportUsers"] = {}
        users_obj = Users(self.v4_api_util)
        try:
            users = users_obj.list_users()
            name_type_set = set([(user.get("username"),user.get("user_type")) for user in users])
            for user in self.users:
                self.results["ImportUsers"][user["username"]] = "CAN'T VERIFY"
                if (user["username"], user["user_type"]) in name_type_set:
                    self.results["ImportUsers"][user["username"]] = "PASS"
                else:
                    self.results["ImportUsers"][user["username"]] = "FAIL"
        except Exception as e:
            self.logger.debug(e)
            self.logger.info(f"Exception occurred during the verification of {type(self).__name__!r}")