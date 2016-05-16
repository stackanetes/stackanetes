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

from kolla_k8s.config import k8s
from kolla_k8s.config import kolla
from kolla_k8s.config import logging
from kolla_k8s.config import network
from kolla_k8s.config import profiles
from kolla_k8s.config import service
from kolla_k8s.config import zookeeper


def list_opts():
    return [
        ('k8s', k8s.k8s_opts),
        ('kolla', kolla.kolla_opts),
        ('network', network.network_opts),
        ('profiles', profiles.profiles_opts),
        ('service', service.service_opts),
        ('zookeeper', zookeeper.zookeeper_opts),
        ('', logging.logging_opts)
    ]
