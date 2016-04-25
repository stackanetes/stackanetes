# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import netifaces
from oslo_config import cfg


CONF = cfg.CONF
CONF.import_group('network', 'kolla_k8s.config.network')


def _get_localhost():
    """Get localhost IP address regarding the IP protocol version"""
    if CONF.network.ipv6:
        return '::1'
    return '127.0.0.1'


def get_ip_address(public=False):
    """Get IP address of the interface connected to the network.

    If there is no such an interface, then localhost is returned.
    """
    if public:
        iface = CONF.network.public_interface
    else:
        iface = CONF.network.private_interface

    if iface not in netifaces.interfaces():
        return _get_localhost()

    if CONF.network.ipv6:
        address_family = netifaces.AF_INET6
    else:
        address_family = netifaces.AF_INET

    for ifaddress in netifaces.ifaddresses(iface)[address_family]:
        if 'addr' in ifaddress:
            return ifaddress['addr']

    return _get_localhost()
