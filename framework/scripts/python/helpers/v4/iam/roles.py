from typing import Union, List, Dict, Optional
from framework.helpers.v4_api_client import ApiClientV4

import ntnx_iam_py_client

class Roles:
    kind = "roles"
    # Configure the client
    def __init__(self, v4_api_util: ApiClientV4):
        self.resource_type = "iam/v4.0/authz/roles"
        self.client = v4_api_util.get_api_client("iam")
        self.roles_api = ntnx_iam_py_client.RolesApi(
            api_client=self.client
            )

    def get_by_display_name(self, display_name: str) -> Union[List, Dict]:
        """
        Get a role by its display name.  
        Args:  
          display_name (str): The display name of the role to retrieve.  
        Returns:  
          dict: The role object if found, otherwise an empty list.  
        """

        entity = self.roles_api.list_roles(_filter=f"displayName eq '{display_name}'").to_dict()["data"]
        if entity:
            return entity[0]
        return entity

    def add_role(self, display_name: str, description: str, operations: List[str]) -> Dict:
        """
        Add role to objects
          display_name(str): The name of role
          description(str): The description
          operations(List): The list of operations uuids
        Returns:
          dict: The API response
        """
        role = ntnx_iam_py_client.Role(
            display_name=display_name,
            description=description,
            operations=operations
        )
        return self.roles_api.create_role(
            body= role
            )