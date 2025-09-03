from typing import Union, List, Dict
from framework.helpers.v4_api_client import ApiClientV4

import ntnx_iam_py_client

class Users:
    kind = "users"
    # Configure the client
    def __init__(self, v4_api_util: ApiClientV4):
        self.resource_type = "iam/v4.0/authn/users"
        self.client = v4_api_util.get_api_client("iam")
        self.users_api = ntnx_iam_py_client.UsersApi(
            api_client=self.client
            )

    def get_by_username_and_type(self, username: str, type: str) -> Union[None, Dict]:
        """
        Get user by username and type
        Args:
          username(str): the username
          type(str): the user type
        Returns:
          dict: The user object
        """ 
        entities = self.users_api.list_users().to_dict()["data"]
        entity = [e for e in entities if e.get("username") == username and e.get("user_type") == type] or None
        if entity:
            return entity[0]
        return entity
    
    def list_users(self) -> List[Dict]:
        """
        List all users
        Returns:
          list: List of users
        """
        users = self.users_api.list_users().to_dict()["data"]
        return users
  
    def import_user(self, username: str, user_type: str, idp_uuid: str) -> Dict:
      """
        Import user to PC
        
        username(str): The username
        user_type(str): The user type
        idp(str): The IDP
        Returns:
        dict: The API response
        """

      user = ntnx_iam_py_client.User(
          username=username,
          user_type=user_type,
          idp_id=idp_uuid,
      )
      return self.users_api.create_user(
          body= user
          )

    def add_user(self, username: str, user_type: str, first_name: str, last_name: str, email: str, password: str) -> Dict:
        """
        Add user to objects
          username(str): The username
          user_type(str): The user type
          first_name(str): The first name
          last_name(str): The last name
          email(str): The email
          password(str): The password
        Returns:
          dict: The API response
        """
        user = ntnx_iam_py_client.User(
            username=username,
            user_type=user_type,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        return self.users_api.create_user(
            body= user
            )
    
    def get_users_ext_id_list(self, users: Dict) -> List[str]:
        """
        Get users uuid list
          users(Dict): {User_type: [user1, user2]}
        Returns:
          list: List of uuids
        """
        user_uuids = []
        for user_type, usernames in users.items():
            for username in usernames:
              users_response = self.users_api.list_users(_filter=f"username eq '{username}'")
              user = next(
                  (user for user in users_response.data if user.user_type == user_type), None
                )
              if user:
                user_uuids.append(user.ext_id)
              else:
                raise Exception(f"User with username {username} and type {user_type} not found")
        return user_uuids

    def create_iam_key(self, user_ext_id: str, key_type: str, name: str, description: str) -> Dict:
        """
        Create IAM Key
          user_ext_id(str): The user ext id
          key_type(str): The key type
          name(str): The name
          description(str): The description
        Returns:
          dict: The API response
        """
        iam_key = ntnx_iam_py_client.Key(
            key_type=key_type,
            name=name,
            description=description
        )
        return self.users_api.create_user_key(
            userExtId = user_ext_id,
            body = iam_key
            )
    
    def list_iam_keys(self, user_ext_id) -> List[Dict]:
        """
        List IAM Keys
        Returns:
          list: List of IAM Keys
        """
        return self.users_api.list_user_keys(userExtId=user_ext_id).to_dict()["data"]