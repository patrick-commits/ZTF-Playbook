from typing import Union, List, Dict
from framework.helpers.v4_api_client import ApiClientV4

import ntnx_iam_py_client

class DirectoryServices:
    kind = "directory_services"
    # Configure the client
    def __init__(self, v4_api_util: ApiClientV4):
        self.resource_type = "iam/v4.0/authn/directory-services"
        self.client = v4_api_util.get_api_client("iam")
        self.directory_services_api = ntnx_iam_py_client.DirectoryServicesApi(
            api_client=self.client
            )

    def get_by_domain_name(self, domain_name: str) -> Union[List, Dict]:
        """
        Get directory service by domain name
        Args:
          domain_name(str): the domain name
        Returns:
          list
        """
        entities = self.directory_services_api.list_directory_services().to_dict()["data"]
        entity = [e for e in entities if e.get("domain_name") == domain_name] or None
        if entity:
            return entity[0]
        return entity

    def get_uuid_by_directory_service_name(self, directory_name: str) -> Union[None, str]:
        """
        Get uuid by directory service name
        Args:
          directory_name(str): the directory service name
        Returns:
          str
        """
        entities = self.directory_services_api.list_directory_services(_filter=f"name eq '{directory_name}'").data
        if entities:
            return entities[0].ext_id
        return None

    def add_directory_service(self, name: str, domain_name: str, url: str, service_account_username: str,
                              service_account_password: str) -> Dict:
        """
        Add directory service to objects
          ad_name(str): The name of directory service
          ad_domain(str): The domain name
          name(str): The name of directory service
          domain_name(str): The domain name
          url(str): The ip address of the domain
          service_account_username(str): The username
          service_account_password(str): The password
        Returns:
          dict: The API response
        """
        if domain_name not in service_account_username:
            service_account_username = f"{service_account_username}@{domain_name}"

        directoryService = ntnx_iam_py_client.DirectoryService(
            name=name,
            domain_name=domain_name,
            directory_type=ntnx_iam_py_client.DirectoryType.ACTIVE_DIRECTORY,
            url=url,
            service_account=ntnx_iam_py_client.DsServiceAccount(
                username=service_account_username,
                password=service_account_password
            )
        )
        return self.directory_services_api.create_directory_service(
            body= directoryService
            )
    
    def get_distinguished_name_user(self, directory_service_name: str, username: str) -> Union[None, Dict]:
        """
        Search and get distinguished name
          domain_name(str): The domain name
          username(str): Name of the User
        Returns:
          dict: The API response
        """
        directory_service_uuid = self.get_uuid_by_directory_service_name(directory_service_name)
        if not directory_service_uuid:
            raise Exception(f"Directory service with name {directory_service_name} not found")
        search_result = self.directory_services_api.search_directory_service(
            extId=directory_service_uuid,
            body=ntnx_iam_py_client.DirectoryServiceSearchQuery(query=username)
        )
        if search_result.data.search_results:
            for result in search_result.data.search_results:
                if result.entity_type == "Person":
                    return result
        return None

    def get_distinguished_name_user_group(self, directory_service_uuid: str, name: str) -> Union[None,str]:
        """
        Get distinguished name
        Args:
          directory_service_uuid(str): The directory service uuid
          name(str): The name
        Returns:
          The distinguished name if found, otherwise None
        """
        search_result = self.directory_services_api.search_directory_service(
            extId=directory_service_uuid,
            body=ntnx_iam_py_client.DirectoryServiceSearchQuery(query=name)
        )
        if search_result.data.search_results:
            for result in search_result.data.search_results:
                if result.entity_type == "Group":
                    return result.name
        return None