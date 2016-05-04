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
k8s_opts = [
    cfg.StrOpt('host', default=''),
    cfg.StrOpt('kubectl_path', default='/usr/bin/kubectl'),
    cfg.StrOpt('kubeconfig_path', default=''),
    cfg.StrOpt('yml_dir_path', default='rc/')
]
k8s_opt_group = cfg.OptGroup(name='k8s', title="test")
CONF.register_group(k8s_opt_group)
CONF.register_cli_opts(k8s_opts, k8s_opt_group)
CONF.register_opts(k8s_opts, k8s_opt_group)
