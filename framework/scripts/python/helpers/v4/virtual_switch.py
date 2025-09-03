from framework.helpers.v4_api_client import ApiClientV4
import ntnx_networking_py_client

class VirtualSwitch:
    def __init__(self, v4_api_util: ApiClientV4):
        self.client = v4_api_util.get_api_client("network")
        self.virtual_switch_api = ntnx_networking_py_client.VirtualSwitchesApi(
            api_client=self.client
        )

    def list(self):
        return self.virtual_switch_api.list_virtual_switches().to_dict()
    
    def get_vs_uuid(self, name: str):
        response = self.list()
        vs_uuid = None
        for vs in response["data"]:
            if vs["name"] == name:
                vs_uuid = vs["ext_id"]
        if not vs_uuid:
            raise Exception(f"Could not fetch the UUID of the entity {type(self).__name__} with name {name}")
        return vs_uuid