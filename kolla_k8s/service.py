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
from oslo_log import log as logging

from kolla_k8s.k8s_instance import K8sInstance

LOG = logging.getLogger()
CONF = cfg.CONF
CONF.import_group('stackanetes', 'kolla_k8s.config.stackanetes')

# TODO: load this services lists from config
COMPUTE_SERVICES = ['nova-compute', 'nova-libvirt', 'openvswitch-vswitchd',
                    'neutron-openvswitch-agent', 'openvswitch-db']
NETWORK_SERVICES = ['neutron-openvswitch-agent', 'neutron-dhcp-agent',
                    'neutron-metadata-agent', 'openvswitch-vswitchd',
                    'openvswitch-db', 'neutron-l3-agent']
OTHER_SERVICES = ['keystone-init', 'keystone-api', 'keystone-db-sync',
                  'glance-init', 'mariadb', 'rabbitmq', 'glance-registry',
                  'glance-api', 'nova-init', 'nova-api', 'nova-scheduler',
                  'nova-conductor', 'nova-consoleauth', 'neutron-init',
                  'neutron-server', 'horizon-filebased']


# Public API below
##################
def run_service(service_name, service_dir):
    if service_name == "all":
        service_list = OTHER_SERVICES[:]
        service_list.extend(["compute-node", "network-node"])
    else:
        service_list = [service_name]

    for service in service_list:
        instance = K8sInstance(service, service_dir)
        instance.run()


def kill_service(service_name, service_dir):
    if service_name == "all":
        service_list = OTHER_SERVICES[:]
        service_list.extend(["compute-node", "network-node"])
    else:
        service_list = [service_name]

    for service in service_list:
        instance = K8sInstance(service, service_dir)
        instance.delete()
