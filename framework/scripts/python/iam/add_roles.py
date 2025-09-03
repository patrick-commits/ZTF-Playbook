from typing import Dict
from framework.helpers.log_utils import get_logger
from framework.helpers.v4_api_client import ApiClientV4
from framework.scripts.python.script import Script
from framework.scripts.python.helpers.v4.iam.roles import Roles
from framework.scripts.python.helpers.v4.iam.operations import Operations

logger = get_logger(__name__)

class AddRoles(Script):
    """
    Class that adds Roles in IAM
    """
    def __init__(self, data: Dict, **kwargs):
        self.data = data
        self.roles = self.data.get("roles", [])
        self.v4_api_util = self.data["v4_api_util"]
        super(AddRoles, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            iam_roles_obj = Roles(self.v4_api_util)
            iam_operations_obj = Operations(self.v4_api_util)

            if self.roles:
                for role in self.roles:
                    # Check if role already exists
                    # If it exists, skip
                    if iam_roles_obj.get_by_display_name(role.get("display_name")):
                        self.logger.warning(f"SKIP: Role with display_name {role['display_name']} is "
                                            f"already present in {self.data['pc_ip']!r}")
                        continue
                    else:
                        operations = []
                        for operation in role.get('operations'):
                            if not iam_operations_obj.get_uuid_by_name(operation):
                                self.exceptions.append(
                                    f"Operation with display name {operation} not found for role {role.get('display_name')}"
                                    )
                                continue
                            else:
                                operations.append(iam_operations_obj.get_uuid_by_name(operation))

                        response = iam_roles_obj.add_role(
                            display_name=role["display_name"],
                            description=role.get("description", None),
                            operations=operations,
                        )
                        logger.debug(response)
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        if not self.roles:
            return

        self.results["Roles"] = {}
        for role in self.roles:
            # Initial status
            self.results["Roles"][role["display_name"]] = "CAN'T VERIFY"

            iam_roles_obj = Roles(self.v4_api_util)

            try:
                if iam_roles_obj.get_by_display_name(role["display_name"]):
                    self.results["Roles"][role["display_name"]] = "PASS"
                else:
                    self.results["Roles"][role["display_name"]] = "FAIL"
            except Exception as e:
                self.exceptions.append(e)