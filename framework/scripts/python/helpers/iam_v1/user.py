from typing import Dict
from framework.helpers.rest_utils import RestAPIUtil
from ..iam_entity import IamEntity


class IamUser(IamEntity):
    """
    Class to change the default system password
    """
    def __init__(self, session: RestAPIUtil, proxy_cluster_uuid=None):
        self.resource_type = "/users"
        super(IamUser, self).__init__(session=session, proxy_cluster_uuid=proxy_cluster_uuid)

    def change_default_admin_password(self, old_password, new_password) -> Dict:
        endpoint = "password"
        data = {
            "old_password":  old_password,
            "new_password": new_password,
            "username": "admin"
        }
        return self.update(data=data, endpoint=endpoint)
