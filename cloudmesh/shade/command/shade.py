from __future__ import print_function

from collections import OrderedDict
from pprint import pprint

import humanize
import timestring
# noinspection PyUnresolvedReferences
from cloudmesh.common.FlatDict import FlatDict2
# noinspection PyUnresolvedReferences
from cloudmesh.common.FlatDict import flatten, flatme
# noinspection PyUnresolvedReferences
from cloudmesh.common.Printer import Printer
# noinspection PyUnresolvedReferences
from cloudmesh.common.default import Default
# noinspection PyUnresolvedReferences
from cloudmesh.common.error import Error
# noinspection PyUnresolvedReferences
from cloudmesh.common.util import path_expand
# noinspection PyUnresolvedReferences
from cloudmesh.common.util import readfile
# noinspection PyUnresolvedReferences
from cloudmesh.shell.command import PluginCommand
# noinspection PyUnresolvedReferences
from cloudmesh.shell.command import command
from ruamel import yaml

from cloudmesh.openstack.api import OpenStack


class OpenstackCommand(PluginCommand):
    # noinspection PyUnusedLocal
    @command
    def do_openstack(self, args, arguments):
        """
        ::

          Usage:
                openstack info
                openstack yaml 
                openstack yaml list [CLOUD] 
                openstack image list [CLOUD] [--format=FORMAT]
                openstack flavor list [CLOUD] [--format=FORMAT]
                openstack vm list [CLOUD] [--user=USER] [--format=FORMAT] [--ip=public|private]

          This command does some useful things.

          Arguments:
              FILE   a file name
            
          Options:
              -f      specify the file

        """
        # print(arguments)

        default = Default()
        cloud = arguments.CLOUD or default["global"]["cloud"]
        default.close()
        arguments.format = arguments["--format"] or 'table'

        arguments.user = arguments["--user"]

        if arguments.info:

            if arguments.CLOUD is None:
                arguments.CLOUD = cloud

            provider = OpenStack(arguments.CLOUD)
            provider.information()

        elif arguments.yaml and arguments.list:

            filename = path_expand("~/.cloudmesh/cloudmesh.yaml")
            content = readfile(filename)
            d = yaml.load(content, Loader=yaml.RoundTripLoader)
            if arguments.CLOUD is None:
                default_cloud = default["global"]["cloud"]

                # print (yaml.dump(d, indent=4, Dumper=yaml.RoundTripDumper))
                info = OrderedDict()
                clouds = d["cloudmesh"]["clouds"]
                for cloud in clouds:
                    info[cloud] = {
                        "default": "",
                        "name": cloud,
                        "type": clouds[cloud]["cm_type"],
                        "label": clouds[cloud]["cm_label"],
                        "flavor": clouds[cloud]["default"]["flavor"],
                        "image": clouds[cloud]["default"]["image"]
                    }
                    if default_cloud == cloud:
                        info[cloud]["default"] = "*"

                print(Printer.dict(info,
                                   order=["default", "name", "type", "label", "flavor", "image"]))

            else:
                cloud = arguments.CLOUD
                clouds = d["cloudmesh"]["clouds"]
                print(yaml.dump(clouds[cloud], indent=4, Dumper=yaml.RoundTripDumper))

        elif arguments.yaml:

            filename = path_expand("~/.cloudmesh/cloudmesh.yaml")
            content = readfile(filename)
            d = yaml.load(content, Loader=yaml.RoundTripLoader)
            print(yaml.dump(d, indent=4, Dumper=yaml.RoundTripDumper))

        elif arguments.image and arguments.list:

            if arguments.CLOUD is None:
                arguments.CLOUD = cloud

            # print (arguments.CLOUD)

            provider = OpenStack(arguments.CLOUD)
            images = provider.images()

            try:
                fd = flatme(images)
            except Exception as e:
                Error.traceback(error=e, debug=True, trace=True)

            order = ["name", "extra__metadata__user_id", "extra__metadata__image_state", "extra__updated"]
            header = ["name", "user", "state", "updated"]

            if arguments.format == "table":
                print(arguments.CLOUD)
                print(Printer.dict(fd,
                                   sort_keys="name",
                                   order=order,
                                   header=header,
                                   output=arguments.format))
            # elif arguments.format == "dict":
            #    print(yaml.dump(images, indent=4, Dumper=yaml.RoundTripDumper))
            else:
                print(Printer.dict(images, output=arguments.format))

        elif arguments.flavor and arguments.list:

            if arguments.CLOUD is None:
                arguments.CLOUD = cloud

            # print (arguments.CLOUD)

            provider = OpenStack(arguments.CLOUD)
            d = provider.flavors()
            print(arguments.CLOUD)
            print(Printer.dict(d,
                               sort_keys="id",
                               output=arguments.format,
                               order=['id', 'name', 'ram', 'vcpus', 'disk']))

        elif arguments.vm and arguments.list:

            if arguments.CLOUD is None:
                arguments.CLOUD = cloud

            # print (arguments.CLOUD)

            provider = OpenStack(arguments.CLOUD)
            elements = provider.vms()

            if arguments.user is not None:
                found = {}
                for element in elements:
                    if elements[element]['extra']['userId'] == arguments.user:
                        found[element] = elements[element]
                elements = found

            try:
                fd = flatme(elements)
            except Exception as e:
                Error.traceback(error=e, debug=True, trace=True)

            order = ["name", 'extra__vm_state', 'extra__metadata__image', 'extra__metadata__flavor', "extra__key_name",
                     'extra__metadata__group', "extra__userId", "extra__created", 'private_ips', 'public_ips']
            header = ["name", "state", "image", "flavor", "key", "group", "user", "created", "private", "public"]

            if arguments.format == "table" or arguments.format == "inventory":

                for element in fd:
                    fd[element]['private_ips'] = ','.join(fd[element]['private_ips'])
                    fd[element]['public_ips'] = ','.join(fd[element]['public_ips'])
                    # fd[element]["extra__created"] = humanize.timedelta(fd[element]["extra__created"])
                    t = humanize.naturaltime(timestring.Date(fd[element]["extra__created"]).date)
                    fd[element]["extra__created"] = t

                if arguments["--ip"]:

                    kind = arguments["--ip"]

                    ips = {}
                    for element in fd:
                        ips[element] = {
                            'name': fd[element]['name'],
                            kind: fd[element][kind + '_ips']
                        }
                    if arguments.format == 'inventory':
                        # print ("[hosts]")
                        for host in ips:
                            print (ips[host][kind])
                    else:
                        print(Printer.dict(ips,
                                   # sort_keys=True,
                                   order=["name", kind],
                                   output=arguments.format))

                else:
                    print(arguments.CLOUD)
                    print(Printer.dict(fd,
                                       # sort_keys=True,
                                       order=order,
                                       header=header,
                                       output=arguments.format))
                # elif arguments.format == "dict":
                #    print(yaml.dump(images, indent=4, Dumper=yaml.RoundTripDumper))
            elif arguments.format == 'flatten':
                pprint(fd)
            else:
                print(Printer.dict(elements, output=arguments.format))

            return ""