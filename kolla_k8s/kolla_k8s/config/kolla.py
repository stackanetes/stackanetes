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

from kolla_k8s.common import utils


CONF = cfg.CONF
kolla_opts = [
    cfg.StrOpt('namespace',
               default='kollaglue',
               help='The Docker namespace name'),
    cfg.StrOpt('tag',
               default='1.0.0',
               help='The Docker tag'),
    cfg.StrOpt('base',
               default='centos',
               help='The base distro which was used to build images'),
    cfg.StrOpt('base-tag',
               default='latest',
               help='The base distro image tag'),
    cfg.StrOpt('install-type',
               default='binary',
               help='The method of the OpenStack install'),
    cfg.StrOpt('deployment-id',
               default=utils.env('USER', default='default'),
               help='Uniq name for deployment'),
    cfg.StrOpt('profile',
               default='default',
               help='Build profile which was used to build images')
]
kolla_opt_group = cfg.OptGroup(name='kolla',
                               title='Options for Kolla Docker images')
CONF.register_group(kolla_opt_group)
CONF.register_cli_opts(kolla_opts, kolla_opt_group)
CONF.register_opts(kolla_opts, kolla_opt_group)
