from typing import Dict
from framework.helpers.log_utils import get_logger
from framework.scripts.python.helpers.v4.iam.users import Users
from framework.scripts.python.helpers.v4.iam.directory_services import DirectoryServices
from framework.scripts.python.script import Script

logger = get_logger(__name__)


class CreateIAMKeys(Script):
    """
    Class that creates IAM Keys
    """
    def __init__(self, data: Dict, **kwargs):
        self.data = data
        self.v4_api_util = self.data["v4_api_util"]
        self.iam_keys = self.data.get("iam_keys")
        super(CreateIAMKeys, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            users_obj = Users(self.v4_api_util)

            if self.iam_keys:
                for key in self.iam_keys:
                    user_ext_id = users_obj.get_by_username_and_type(key["user"]["username"], key["user"]["user_type"]).get("ext_id")
                    if not user_ext_id:
                        self.exceptions.append(f"User with username {key['user']['username']} not found")
                        continue
                    user_keys = users_obj.list_iam_keys(user_ext_id=user_ext_id)
                    user_keys_name_list = [user_key["name"] for user_key in user_keys]
                    if key["name"] in user_keys_name_list:
                        self.logger.warning(f"SKIP: IAM Key with name {key['name']} is "
                                            f"already present in {self.data['pc_ip']!r}")
                        continue
                    else:
                        # Create IAM Key
                        response = users_obj.create_iam_key(
                            user_ext_id=user_ext_id,
                            key_type=key["key_type"],
                            name=key["name"],
                            description=key["description"]
                            )
                        self.logger.debug(response)
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        if not self.iam_keys:
            return

        self.results["CreateIAMKeys"] = {}
        users_obj = Users(self.v4_api_util)
        try:
            for key in self.iam_keys:
                user_ext_id = users_obj.get_by_username_and_type(key["user"]["username"], key["user"]["user_type"]).get("ext_id")
                user_keys = users_obj.list_iam_keys(user_ext_id=user_ext_id)
                user_keys_name_list = [user_key["name"] for user_key in user_keys]
                if key["name"] in user_keys_name_list:
                    self.results["CreateIAMKeys"][key["name"]] = "PASS"
                else:
                    self.results["CreateIAMKeys"][key["name"]] = "FAIL"
        except Exception as e:
            self.exceptions.append(e)
                