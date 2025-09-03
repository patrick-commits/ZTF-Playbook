from typing import Dict
from framework.helpers.log_utils import get_logger
from framework.scripts.python.helpers.v4.iam.authorization_policy import AuthorizationPolicies
from framework.scripts.python.helpers.v4.iam.roles import Roles
from framework.scripts.python.helpers.v4.iam.users import Users
from framework.scripts.python.helpers.v4.iam.user_groups import UserGroups
from framework.scripts.python.script import Script
from framework.helpers.helper_functions import read_creds

logger = get_logger(__name__)


class AddAuthorizationPolicy(Script):
    """
    Class that adds Authorization Policy in IAM
    """
    def __init__(self, data: Dict, **kwargs):
        self.data = data
        self.v4_api_util = self.data["v4_api_util"]
        self.auth_policies = self.data.get("authorization_policies", [])
        super(AddAuthorizationPolicy, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            auth_policy_obj = AuthorizationPolicies(self.v4_api_util)
            roles_obj = Roles(self.v4_api_util)
            users_obj = Users(self.v4_api_util)
            user_groups_obj = UserGroups(self.v4_api_util)

            if self.auth_policies:
                for auth_policy in self.auth_policies:

                    if auth_policy_obj.get_by_display_name(auth_policy.get("display_name")):
  
                        self.logger.warning(f"SKIP: Authorization Policy with display_name {auth_policy['display_name']} is "
                                            f"already present in {self.data['pc_ip']!r}")
                        continue

                    role_ext_id = roles_obj.get_by_display_name(auth_policy.get("role"))["ext_id"]
                    if not role_ext_id:
                        self.exceptions.append(f"Role with display name {auth_policy.get('role')} not found")

                    identities = {}
                    try:
                        if auth_policy["identities"].get("users"):
                            identities['user_ext_ids'] = users_obj.get_users_ext_id_list(auth_policy["identities"]["users"])
                        if auth_policy["identities"].get("user_groups"):
                            identities['user_group_ext_ids'] = user_groups_obj.get_user_groups_ext_id_list(auth_policy["identities"]["user_groups"])
                    except Exception as e:
                        self.exceptions.append(e)
                        continue
                    if not identities:
                        self.exceptions.append(f"Exception on finding Given User or User Group in PC")
                        continue
                    response = auth_policy_obj.add_authorization_policy(
                        display_name=auth_policy["display_name"],
                        description=auth_policy.get("description", None),
                        role=role_ext_id,
                        identities=identities,
                    )

                    logger.debug(response)
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        if not self.auth_policies:
            return
        # Initialize the results dictionary for Authorization Policies  
        self.results["AuthorizationPolicies"] = {}  

        for auth_policy in self.auth_policies:  
            # Initial status  
            self.results["AuthorizationPolicies"][auth_policy["display_name"]] = "CAN'T VERIFY"


            auth_policy_obj = AuthorizationPolicies(self.v4_api_util)

            try:
                if auth_policy_obj.get_by_display_name(auth_policy.get("display_name")):
                    self.results["AuthorizationPolicies"][auth_policy["display_name"]] = "PASS"
                else:
                    self.results["AuthorizationPolicies"][auth_policy["display_name"]] = "FAIL"
            except Exception as e:
                self.logger.debug(e)
                self.logger.info(f"Exception occurred during the verification of {type(self).__name__!r}")