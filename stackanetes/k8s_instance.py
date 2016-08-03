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
CONF.import_group('ceph','stackanetes.config.ceph')


class K8sInstance(object):
    def __init__(self, service_name, service_dir):
        LOG.debug("Creating instance: {}".format(service_name))
        self.service_name = service_name
        self.service_type = service_name.split("-")[0]
        self.service_dir = service_dir
        self._load_service_variables()
        if not check_if_namespace_exist(self.namespace):
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
        self.ceph_required = variables.get('ceph_required', False)
        self.centralized_logging_required = variables.get('centralized_logging_required', False)
        self.configs = variables
        self.files = variables.get('files', [])
        self.containers = variables.get('containers', [])
        self.namespace = variables.get('namespace', CONF.stackanetes.namespace)
        LOG.error("k8s_instances: {}".format(self.namespace))

    def _load_configmaps(self):
        if self.containers:
            files = []
            [files.extend(x.get('files', [])) for x in self.containers]
            for file_configuration in files:
                LOG.debug("Preparing configmap: {} for {}".format(
                    file_configuration['configmap_name'], self.service_name))
                file_configuration['namespace'] = self.namespace
                configmap = ConfigMap(self.service_dir, file_configuration)
                configmap.remove()
                configmap.upload()

        for file_configuration in self.files:
            LOG.debug("Preparing configmap: {} for {}".format(
                file_configuration['configmap_name'], self.service_name))
            file_configuration['namespace'] = self.namespace
            configmap = ConfigMap(self.service_dir, file_configuration)
            configmap.remove()
            configmap.upload()

    def _generate_manifest(self):
        LOG.debug("Start generating manifest: {}".format(self.configs.get(
            "name", "[Cannot get manifest name]")))
        manifest = Manifest(self.configs, self.service_dir)
        data = manifest.render()
        self.file_path = os.path.join("/tmp", self.service_name + ".yml")
        with open(self.file_path, 'w') as stream:
            stream.write(data)

    def _check_if_ceph_conditional_is_fulfilled(self):
        return False if not CONF.ceph.ceph_enabled and \
                        self.ceph_required else True
    
    def _check_if_central_log_conditional_is_fulfilled(self):
        return False if not CONF.stackanetes.centralized_logging and \
                        self.centralized_logging_required else True

    def run(self):
        LOG.debug("Calling run on {}".format(self.service_name))
        if not self._check_if_ceph_conditional_is_fulfilled():
            LOG.warning(
                "{} requires CEPH to working but CEPH is disabled.".format(
                    self.service_name.capitalize()
                ))
            return
        if not self._check_if_central_log_conditional_is_fulfilled():
            LOG.warning(
                "{} requires centralized logging to working but it is disabled.".format(
                    self.service_name.capitalize()
                ))
            return
        self._generate_manifest()
        self._manage_instance("create")

    def delete(self):
        LOG.debug("Calling delete on {}".format(self.service_name))
        self._generate_manifest()
        self._manage_instance("delete")

    def _manage_instance(self, cmd_type):
        LOG.debug("{}ing {}".format(cmd_type[:-1], self.service_name))
        cmd = get_kubectl_command(self.namespace)

        cmd.extend([cmd_type, "-f", self.file_path])
        LOG.debug('{} instance {}'.format(cmd_type, self.service_name))
        subprocess.call(cmd)

