from typing import Union, List, Dict
from framework.helpers.v4_api_client import ApiClientV4

import ntnx_iam_py_client

class AuthorizationPolicies:
    kind = "authorization_policies"
    # Configure the client
    def __init__(self, v4_api_util: ApiClientV4):
        self.resource_type = "iam/v4.0/authz/authorization-policies"
        self.client = v4_api_util.get_api_client("iam")
        self.authorization_policy_api = ntnx_iam_py_client.AuthorizationPoliciesApi(
            api_client=self.client
            )

    def get_by_display_name(self, display_name: str) -> Union[List, Dict]:
        """
        Get an authorization policy by its display name.  
        Args:  
          display_name (str): The display name of the authorization policy.  
        Returns:  
          dict or None: The authorization policy if found, otherwise None. 
        """

        entities = self.authorization_policy_api.list_authorization_policies().to_dict()["data"]
        entity = [e for e in entities if e.get("display_name") == display_name] or None
        if entity:
            return entity[0]
        return entity

    def get_identities(self, identities: List) -> List:
        """
        Get users uuid list
          users(Dict): {User_type: [usergroup1, usergroup2]}
        Returns:
        Processes the provided identities dictionary and returns a list of IdentityFilter objects
        for users and user groups.

        Args:
          identities (Dict): Dictionary with keys 'user_ext_ids' and/or 'user_group_ext_ids' containing lists of external IDs.

        Returns:
          list: List of ntnx_iam_py_client.IdentityFilter objects representing identity filters.
        """
        identities_result = []
        if identities.get("user_ext_ids"):
            user = ntnx_iam_py_client.IdentityFilter(
                identity_filter = {
                    "user": {
                        "uuid": {
                            "anyof": identities['user_ext_ids']
                        }
                    }
                }
            )
            identities_result.append(user)

        if identities.get("user_group_ext_ids"):
            identities_result.append(
                ntnx_iam_py_client.IdentityFilter(
                    identity_filter = {
                        "user": {
                            "group": {
                                "anyof": identities['user_group_ext_ids']
                            }
                        }
                    }
                )
            )
        return identities_result

    def get_entities(self, entities: List=None) -> List:
        return [
            ntnx_iam_py_client.EntityFilter(
                entity_filter={
                    "*":{"*":{"eq":"*"}}
                    }
            )
        ]

    def add_authorization_policy(self, display_name: str, description: str, 
                                 role: str, identities: Dict) -> Dict:
        """
        Add IAM Authorization Policy
          display_name(str): The name of directory service
          description(str): The domain name
          role(str): The ip address of the domain
        Returns:
          dict: The API response
        """
        authorization_policy = ntnx_iam_py_client.AuthorizationPolicy(
            display_name=display_name,
            description=description,
            role=role,
            entities=self.get_entities(),
            identities=self.get_identities(identities)
            )
        return self.authorization_policy_api.create_authorization_policy(
            body= authorization_policy
            )