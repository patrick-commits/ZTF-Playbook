from typing import Union, List, Dict, Optional
from framework.helpers.v4_api_client import ApiClientV4

import ntnx_iam_py_client

class Operations:
    kind = "operations"
    # Configure the client
    def __init__(self, v4_api_util: ApiClientV4):
        self.resource_type = "iam/v4.0/authz/operations"
        self.client = v4_api_util.get_api_client("iam")
        self.operations_api = ntnx_iam_py_client.OperationsApi(
            api_client=self.client
            )

    def get_uuid_by_name(self, name: str = None) -> Optional[str]:
        """
        Get operation uuid by name
            name(str): The name of operation
        Returns: 
        Optional[str]: The UUID of the operation if found, otherwise None
        """
        response = self.operations_api.list_operations(_filter=f"displayName eq '{name}'")
        if response.data:
            return response.data[0].ext_id
        return None