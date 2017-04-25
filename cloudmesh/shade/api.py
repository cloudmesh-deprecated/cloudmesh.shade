from __future__ import print_function

import warnings

import libcloud
import libcloud.security
import requests
# noinspection PyUnresolvedReferences
from cloudmesh.common.config import Config
# noinspection PyUnresolvedReferences,PyUnresolvedReferences
from cloudmesh.common.default import Default
# noinspection PyUnresolvedReferences
from cloudmesh.common.dotdict import dotdict
# noinspection PyUnresolvedReferences
from cloudmesh.common.error import Error
# noinspection PyUnresolvedReferences,PyUnresolvedReferences
from cloudmesh.common.util import path_expand
# noinspection PyUnresolvedReferences
from cloudmesh.common.util import readfile
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from ruamel import yaml

warnings.simplefilter("ignore")


# warnings.warn(libcloud.security.VERIFY_SSL_DISABLED_MSG)

class OpenStack(object):
    def __init__(self, cloud=None):

        if cloud is None:
            default = Default()
            cloud = default["global"]["cloud"]
            default.close()

        self.info = Config().cloud(cloud)

        # print(yaml.dump(self.info, indent=4, Dumper=yaml.RoundTripDumper))

        self.driver = None
        self.authenticate()

    def authenticate(self):
        libcloud.security.VERIFY_SSL_CERT = False

        provider = get_driver(Provider.OPENSTACK)

        credentials = dotdict(self.info["credentials"])
        # print (credentials)
        # print ("U", credentials.OS_USERNAME)
        self.credentials = credentials

        """
        #chameleon
        self.driver = provider(
            credentials.OS_USERNAME,
            credentials.OS_PASSWORD,
            ex_force_auth_url=credentials.OS_AUTH_URL,
            ex_force_auth_version="3.x_password",
            #ex_force_auth_version="3.x_password",
            ex_tenant_name=credentials.OS_TENANT_NAME,
            # ex_domain_name=credentials.OS_PROJECT_DOMAIN_ID,
            ex_force_service_type='compute',
            ex_force_service_region=credentials.OS_REGION_NAME)
        """
        try:
            self.driver = provider(
                credentials.username,
                credentials.password,
                **credentials)
        except Exception as e:
            Error.traceback(error=e, debug=True, trace=True)

    def _list(self, data):
        d = {}

        for image in data:
            # print (image.__dict__)
            d[image.name] = image.__dict__
            del d[image.name]["_uuid"]
            del d[image.name]["driver"]

        return d

    def information(self):
        print("LLL")
        print(self.credentials.OS_AUTH_URL)

        r = requests.get(self.credentials.OS_AUTH_URL)
        print(r.json())

        print(yaml.dump(r.json(), indent=4, Dumper=yaml.RoundTripDumper))

        url = "https://iu.jetstream-cloud.org:5000/v3"
        r = requests.get(url)
        print(r.json())

        print(yaml.dump(r.json(), indent=4, Dumper=yaml.RoundTripDumper))

        return None

    def images(self):
        return self._list(self.driver.list_images())

    def flavors(self):
        return self._list(self.driver.list_sizes())

    def vms(self):
        return self._list(self.driver.list_nodes())
