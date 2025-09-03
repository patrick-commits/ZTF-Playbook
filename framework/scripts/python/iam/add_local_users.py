from typing import Dict
from framework.helpers.log_utils import get_logger
from framework.scripts.python.helpers.v4.iam.users import Users
from framework.scripts.python.script import Script

logger = get_logger(__name__)


class AddLocalUsers(Script):
    """
    Class that adds Local Users in IAM
    """
    def __init__(self, data: Dict, **kwargs):
        self.data = data
        self.local_users = self.data.get("local_users", [])
        self.v4_api_util = self.data["v4_api_util"]
        super(AddLocalUsers, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            iam_users_obj = Users(self.v4_api_util)

            if self.local_users:
                for user in self.local_users:
                    
                    if iam_users_obj.get_by_username_and_type(user.get("username"), "LOCAL"):
                        self.logger.warning(f"SKIP: User with username {user['username']} is "
                                            f"already present in {self.data['pc_ip']!r}")
                        continue
                    else:
                        response = iam_users_obj.add_user(
                            username=user["username"],
                            first_name=user["first_name"],
                            last_name=user["last_name"],
                            email=user["email"],
                            password=user["password"],
                            user_type="LOCAL"
                        )
                        logger.debug(response)
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        if not self.local_users:
            return

        self.results["LocalUsers"] = {}
        for local_user in self.local_users:
            # Initial status
            self.results["LocalUsers"][local_user["username"]] = "FAIL"

            iam_users_obj = Users(self.v4_api_util)

            try:
                if iam_users_obj.get_by_username_and_type(local_user["username"], "LOCAL"):
                    self.results["LocalUsers"][local_user["username"]] = "PASS"
                else:
                    self.results["LocalUsers"][local_user["username"]] = "FAIL"
            except Exception as e:
                self.logger.debug(e)
                self.logger.info(f"Exception occurred during the verification of {type(self).__name__!r}")