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

CONTROL_SERVICES = ["glance-api", "glance-registry", "horizon-filebased",
                    "keystone-api", "neutron-server", "nova-api", "mariadb",
                    "nova-conductor", "nova-novncproxy", "nova-scheduler",
                    "rabbitmq", "horizon", "nova-consoleauth"]
INIT_SERVICES = ["glance-init", "keystone-init", "keystone-db-sync",
                 "nova-init", "neutron-init"]

CONF = cfg.CONF
service_opts = [
    cfg.StrOpt('memory', default='4092Mi'),
    cfg.ListOpt('control_services_list', default=CONTROL_SERVICES),
    cfg.ListOpt('init_services_list', default=INIT_SERVICES),
    cfg.ListOpt('glance_api_ports', default=["9292"]),
    cfg.ListOpt('glance_registry_ports', default=["9191"]),
    cfg.ListOpt('horizon_filebased_ports', default=["80, 443"]),
    cfg.ListOpt('keystone_api_ports', default=["5000", "35357"]),
    cfg.ListOpt('mariadb_ports', default=["3306"]),
    cfg.ListOpt('neutron_server_ports', default=["9696"]),
    cfg.ListOpt('nova_api_ports', default=["8774", "8775"]),
    cfg.ListOpt('nova_conductor_ports', default=[]),
    cfg.ListOpt('nova_consoleauth_ports', default=[]),
    cfg.ListOpt('nova_novncproxy_ports', default=["6080"]),
    cfg.ListOpt('nova_scheduler_ports', default=[""]),
    cfg.ListOpt('rabbitmq_ports', default=["5672"]),
    cfg.StrOpt('glance_api_mpath', default="/var/lib/glance:/var/lib/glance"),
    cfg.StrOpt('mariadb_mpath',
               default="/var/lib/openstack-mysql:/var/lib/mysql"),
    cfg.StrOpt('rabbitmq_mpath', default=":/var/log/rabbitmq"),
    cfg.StrOpt('horizon_filebased_external_ip', default=None),
    cfg.StrOpt('nova_novncproxy_external_ip', default=None),

]
service_opt_group = cfg.OptGroup(name='service', title="service")
CONF.register_group(service_opt_group)
CONF.register_cli_opts(service_opts, service_opt_group)
CONF.register_opts(service_opts, service_opt_group)
