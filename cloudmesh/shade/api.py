from __future__ import print_function

import copy
import os
import tempfile
import warnings

import shade
import os_client_config
from ruamel import yaml

from cloudmesh.common.config import Config
from cloudmesh.common.default import Default

warnings.simplefilter("ignore")


def _authenticate(cloud):
    CLOUD_NAME = 'default'

    tmp = tempfile.NamedTemporaryFile()
    try:
        cfg = {
            'clouds': {
                CLOUD_NAME: cloud
                }
            }
        y = yaml.safe_dump(cfg)
        tmp.write(y)
        tmp.seek(0)

        old_env = copy.deep_copy(os.environ)

        try:
            os.environ['OS_CLIENT_CONFIG_FILE'] = tmp.name
            auth = os_client_config.make_shade()
            return auth
        finally:
            os.environ = old_env

    finally:
        tmp.close()


class Shade(object):
    def __init__(self, cloud=None):
        if cloud is None:
            default = Default()
            cloud = default["global"]["cloud"]
            default.close()
        cfg = Config.cloud(cloud)

        self._cloud = _authenticate(cfg)

    def images(self):
        return self._cloud.list_images()

    def flavors(self):
        return self._cloud.list_flavors()

    def vms(self):
        return self._cloud.list_servers()


if __name__ == '__main__':
    s = Shade()
    print(s.images())
    print(s.flavors())
    print(s.vms())
