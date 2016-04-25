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
profiles_opts = [
    # TODO(nihilifer): Add ceph and mongodb when implemented.
    cfg.ListOpt('infra',
                default=['mariadb', 'memcached', 'rabbitmq']),
    # TODO(nihilifer): Add ceilometer, head and swift when implemented.
    cfg.ListOpt('main',
                default=['cinder', 'glance', 'horizon', 'keystone', 'neutron',
                         'nova']),
    # TODO(nihilifer): Enable this profile when any of its services will be
    # implemented.
    # cfg.ListOpt('aux',
    #             default=['designate', 'gnocchi', 'ironic', 'magnum',
    #                      'zaqar']),
    # TODO(nihilifer): Add heat when implemented.
    cfg.ListOpt('default',
                default=['glance', 'horizon', 'keystone', 'memcached',
                         'mariadb', 'neutron', 'nova', 'rabbitmq']),
    # TODO(nihilifer): Add ceph when implemented.
    cfg.ListOpt('gate',
                default=['cinder', 'glance', 'horizon', 'keystone', 'mariadb',
                         'memcached', 'neutron', 'nova', 'rabbitmq'])
]
profiles_opt_group = cfg.OptGroup(name='profiles',
                                  title='Common sets of images')
CONF.register_group(profiles_opt_group)
CONF.register_cli_opts(profiles_opts, profiles_opt_group)
CONF.register_opts(profiles_opts, profiles_opt_group)
