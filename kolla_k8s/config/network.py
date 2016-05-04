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

from oslo_config import cfg


CONF = cfg.CONF
network_opts = [
    cfg.StrOpt('private-interface',
               default='eth0',
               help='NIC connected to the private network'),
    cfg.StrOpt('public-interface',
               default='eth0',
               help='NIC connected to the public network'),
    cfg.BoolOpt('ipv6',
                default=False,
                help='Use IPv6 protocol')
]
network_opt_group = cfg.OptGroup(name='network',
                                 title='Options for network interfaces')
CONF.register_group(network_opt_group)
CONF.register_cli_opts(network_opts, network_opt_group)
CONF.register_opts(network_opts, network_opt_group)
