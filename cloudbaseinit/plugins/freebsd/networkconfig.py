# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Cloudbase Solutions Srl
# Copyright 2012 Iblis Lin <iblis@hs.ntnu.edu.tw>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re

from oslo.config import cfg

from cloudbaseinit import exception
from cloudbaseinit.openstack.common import log as logging
from cloudbaseinit.osutils import factory as osutils_factory
from cloudbaseinit.plugins.common import base

LOG = logging.getLogger(__name__)

opts = [
    cfg.StrOpt('network_adapter', default=None, help='Network adapter to '
               'configure. If not specified, the first available ethernet '
               'adapter will be chosen'),
]

CONF = cfg.CONF
CONF.register_opts(opts)


class NetworkConfigPlugin(base.BasePlugin):
    def execute(self, service, shared_data):
        network_details = service.get_network_details()
        if not network_details:
            return (plugin_base.PLUGIN_EXECUTION_DONE, False)

        address = network_details[0].address
        netmask = network_details[0].netmask
        broadcast = network_details[0].broadcast
        gateway = network_details[0].gateway
        dnsdomain = None
        dnsnameservers = network_details[0].dnsnameservers

        osutils = osutils_factory.get_os_utils()

        network_adapter_name = CONF.network_adapter
        if not network_adapter_name:
            # Get the first available one
            available_adapters = osutils.get_network_adapters()
            LOG.debug('available adapters: %s', available_adapters)
            if not len(available_adapters):
                raise exception.CloudbaseInitException(
                    "No network adapter available")
            network_adapter_name = available_adapters[0]

        LOG.info('Configuring network adapter: \'%s\'' % network_adapter_name)

        reboot_required = osutils.set_static_network_config(
            network_adapter_name, address, netmask, broadcast,
            gateway, dnsdomain, dnsnameservers)

        return (base.PLUGIN_EXECUTION_DONE, reboot_required)
