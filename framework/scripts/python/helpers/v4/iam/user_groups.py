from typing import Union, List, Dict
from framework.helpers.v4_api_client import ApiClientV4

import ntnx_iam_py_client

class UserGroups:
    kind = "users-groups"
    # Configure the client
    def __init__(self, v4_api_util: ApiClientV4):
        self.resource_type = "iam/v4.0/authn/user-groups"
        self.client = v4_api_util.get_api_client("iam")
        self.user_groups_api = ntnx_iam_py_client.UserGroupsApi(
            api_client=self.client
            )
    
    def list_user_groups(self) -> Dict:
        """
        List user groups
        """
        return self.user_groups_api.list_user_groups().to_dict()

    def get_by_name_and_type(self, name: str, group_type: str) -> Union[None, Dict]:
        """
        Get user by name and type
        Args:
          name(str): the name
          group_type(str): the type
        """

        entities = self.user_groups_api.list_user_groups().to_dict()["data"]
        entity = [e for e in entities if e.get("name") == name.lower() and e.get("group_type") == group_type] or None
        if entity:
            return entity[0]
        return entity

    def add_user_group(self, group_type: str, name: str, idp_id: str, distinguished_name: str) -> Dict:
        """
        Add user group to objects
          group_type(str): The group type
          name(str): The name
          idp_id(str): The idp id
          distinguished_name(str): The distinguished name
        Returns:
          dict: The API response
        """
        user_group = ntnx_iam_py_client.UserGroup(
            group_type=group_type,
            name=name,
            idp_id=idp_id,
            distinguished_name=distinguished_name
        )
        try:
            response =  self.user_groups_api.create_user_group(
                            body= user_group
                        )
        except Exception as e:
            raise e
        return response


    def get_user_groups_ext_id_list(self, user_groups: List[Dict]) -> List[str]:
        """
        Get user groups ext id list
        Args:
          user_groups(list): The user groups
        Returns:
          list: The user groups ext id list
        """
        user_groups_ext_id_list = []
        for user_group in user_groups:
            user_group_obj = self.get_by_name_and_type(user_group.get("name"), user_group.get("group_type"))
            if not user_group_obj:
                raise Exception(f"User Group with {user_group} not found")
            else:
                user_groups_ext_id_list.append(user_group_obj["ext_id"])
        return user_groups_ext_id_list