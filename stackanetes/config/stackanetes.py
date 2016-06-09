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
# TODO(DTadrzak): add help information
stackanetes_opts = [
    cfg.StrOpt('context'),
    cfg.StrOpt('docker_image_tag', default='mitaka'),
    cfg.StrOpt('docker_registry', default='quay.io/stackanetes'),
    cfg.StrOpt('host'),
    cfg.StrOpt('kubeconfig_path'),
    cfg.StrOpt('kubectl_path', default='/usr/bin/kubectl'),
    cfg.StrOpt('memory', default='4092Mi'),
    cfg.StrOpt('minion_interface_name', default='eno1'),
    cfg.StrOpt('namespace', default='stackanetes'),
    cfg.StrOpt('dns_ip', default='10.2.0.10'),
    cfg.StrOpt('cluster_name', default='cluster.local'),
    cfg.StrOpt('external_ip', default='10.10.10.10'),
]

stackanetes_opt_group = cfg.OptGroup(name='stackanetes', title="test")
CONF.register_group(stackanetes_opt_group)
CONF.register_cli_opts(stackanetes_opts, stackanetes_opt_group)
CONF.register_opts(stackanetes_opts, stackanetes_opt_group)
