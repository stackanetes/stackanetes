# Copyright 2016 Intel Corporation
#
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

import subprocess
import os
import yaml
from oslo_config import cfg
from oslo_log import log as logging

from stackanetes.configmap import ConfigMap
from stackanetes.manifest import Manifest
from stackanetes.common.utils import (check_if_namespace_exist,
                                      create_namespace, get_kubectl_command)


LOG = logging.getLogger()
CONF = cfg.CONF
CONF.import_group('stackanetes', 'stackanetes.config.stackanetes')


class K8sInstance():
    def __init__(self, service_name, service_dir):
        LOG.debug("Creating instance: {}".format(service_name))
        self.service_name = service_name
        self.service_type = service_name.split("-")[0]
        self.service_dir = service_dir
        self._load_service_variables()
        if not check_if_namespace_exist(CONF.stackanetes.namespace):
            create_namespace(CONF.stackanetes.namespace)
        self._load_configmaps()

    def _load_service_variables(self):
        variables = dict()
        path_to_service_conf = os.path.join(self.service_dir,
                                            self.service_type,
                                            self.service_name + '.yml')
        LOG.debug("Instance: {} loading files from {}".format(
            self.service_name, path_to_service_conf))
        with open(path_to_service_conf, 'r') as file:
            variables.update(yaml.load(file))
        self.configs = variables
        self.files = variables.get('files', [])
        self.containers = variables.get('containers', [])

    def _load_configmaps(self):
        if self.containers:
            files = []
            [files.extend(x.get('files', [])) for x in self.containers]
            for file in files:
                LOG.debug("Preparing configmap: {} for {}".format(
                    file['configmap_name'], self.service_name))
                configmap = ConfigMap(self.service_dir, file)
                configmap.remove()
                configmap.upload()

        for file in self.files:
            LOG.debug("Preparing configmap: {} for {}".format(
                file['configmap_name'], self.service_name))
            configmap = ConfigMap(self.service_dir, file)
            configmap.remove()
            configmap.upload()

    def _generate_manifest(self):
        manifest = Manifest(self.configs, self.service_dir)
        data = manifest.render()
        self.file_path = os.path.join("/tmp", self.service_name + ".yml")
        with open(self.file_path, 'w') as stream:
            stream.write(data)

    def run(self):
        self._generate_manifest()
        self._manage_instance("create")

    def delete(self):
        self._generate_manifest()
        self._manage_instance("delete")

    def _manage_instance(self, cmd_type):
        cmd = get_kubectl_command()

        cmd.extend([cmd_type, "-f", self.file_path])
        LOG.debug('{} instance {}'.format(cmd_type, self.service_name))
        subprocess.call(cmd)


