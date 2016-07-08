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

import os
import subprocess
from oslo_config import cfg


CONF = cfg.CONF
CONF.import_group('stackanetes', 'stackanetes.config.stackanetes')


def env(*args, **kwargs):
    for arg in args:
        value = os.environ.get(arg)
        if value:
            return value
    return kwargs.get('default', '')


def get_kubectl_command():
    cmd = [CONF.stackanetes.kubectl_path]
    if CONF.stackanetes.host:
        server = "--server=" + CONF.stackanetes.host
        cmd.append(server)
    if CONF.stackanetes.kubeconfig_path:
        kubeconfig_path = "--kubeconfig=" + CONF.stackanetes.kubeconfig_path
        cmd.append(kubeconfig_path)
    if CONF.stackanetes.context:
        context = "--context=" + CONF.stackanetes.context
        cmd.append(context)
    if CONF.stackanetes.namespace:
        namespace = "--namespace=" + CONF.stackanetes.namespace
        cmd.append(namespace)

    return cmd


def create_namespace(namespace):
    cmd = get_kubectl_command(add_namespace=False)
    cmd.extend(['create', 'namespace', namespace])
    subprocess.call(cmd)


def check_if_namespace_exist(namespace):
    cmd = get_kubectl_command()
    cmd.extend(['get', 'namespace', namespace])
    output = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE).communicate()[0]
    return True if 'Active' in output else False
