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

import functools
import operator


class MesosClient(object):
    """Decorator and contextmanager for connecting with Mesos."""

    def __enter__(self):
        self.mesos_client = mesos.Client()
        return self.mesos_client

    def __exit__(self, *args, **kwargs):
        pass

    def __call__(self, f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with self as mesos_client:
                return f(mesos_client, *args, **kwargs)
        return wrapper


@MesosClient()
def get_number_of_nodes(mesos_client):
    slaves = mesos_client.get_slaves()
    controller_nodes = 0
    compute_nodes = 0
    storage_nodes = 0

    for slave in slaves:
        if 'openstack_role' not in slave['attributes']:
            continue

        openstack_role = slave['attributes']['openstack_role']
        if openstack_role == 'controller':
            controller_nodes += 1
        elif openstack_role == 'compute':
            compute_nodes += 1
        elif openstack_role == 'storage':
            storage_nodes += 1

    all_nodes = controller_nodes + compute_nodes + storage_nodes

    return controller_nodes, compute_nodes, storage_nodes, all_nodes


@MesosClient()
def get_marathon(mesos_client):
    frameworks = mesos_client.get_frameworks()
    frameworks_names = map(operator.itemgetter('name'), frameworks)
    marathon_framework = None
    for framework_name in frameworks_names:
        if "marathon" in framework_name:
            marathon_framework = framework_name
            break
    return marathon_framework
