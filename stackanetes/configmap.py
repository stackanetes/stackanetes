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

import os
import subprocess
import yaml

from jinja2 import Environment, FileSystemLoader
from stackanetes.common import file_utils
from stackanetes.common.utils import get_kubectl_command
from oslo_config import cfg
from oslo_log import log as logging


LOG = logging.getLogger()
CONF = cfg.CONF
CONF.import_group('stackanetes', 'stackanetes.config.stackanetes')


class ConfigMap(object):
    def __init__(self, service_dir, configs):
        self.service_dir = service_dir
        self.file_name = configs['file_name']
        self.dest_file_name = configs.get('dest_file_name',None)
        self.name = configs['configmap_name']
        self.container_path = configs['container_path']
        self.templates = configs['templates']
        self.variables = {
            'dns_ip': CONF.stackanetes['dns_ip'],
            'cluster_name': CONF.stackanetes['cluster_name'],
            'external_ip': CONF.stackanetes['external_ip'],
            'namespace': CONF.stackanetes['namespace'],
        }

    def _set_type(self, template_path):
        self.type = template_path.split('/')[0]

    def _load_variables(self):
        config_dir = os.path.join(self.service_dir, '..', 'config')
        with open(file_utils.find_config_file('globals.yml'), 'r') as file:
            self.variables.update(yaml.load(file))
        with open(file_utils.find_config_file('passwords.yml'), 'r') as file:
            self.variables.update(yaml.load(file))

        self.variables.update(yaml.load(self._render(config_dir, 'all.yml')))

        proj_yml_dir = os.path.join(config_dir, self.type, 'defaults')
        if os.path.exists(os.path.join(proj_yml_dir, 'main.yml')):
            self.variables.update(yaml.load(self._render(proj_yml_dir,
                                                         'main.yml')))
        else:
            LOG.warning('Path missing %s/main.yml' % proj_yml_dir)

    def _merge_configs(self):
        file = unicode()
        for config_file in self.templates:
            self._set_type(config_file)
            self._load_variables()
            file_path, file_name = os.path.split(config_file)
            config_dir = os.path.join(self.service_dir, '..', 'config',
                                      file_path)
            file += "\n"
            file += self._render(config_dir, file_name)
        return file

    def _create_file(self):
        LOG.debug("Creating file: {}".format(self.file_name))
        if len(self.templates) > 1:
            data = self._merge_configs()
        elif len(self.templates) == 1:
            self._set_type(self.templates[0])
            self._load_variables()
            file_path, file_name = os.path.split(self.templates[0])
            config_dir = os.path.join(self.service_dir, '..', 'config',
                                      file_path)
            data = self._render(config_dir, file_name)
        else:
            LOG.error("You didn't specify path to template for {} file.".format(
                self.file_name
            ))
            raise AttributeError()

        self.file_path = os.path.join("/tmp", self.file_name)

        LOG.debug("Saving file {} to {}".format(self.file_name, self.file_path))
        with open(self.file_path, 'w', 777) as stream:
            os.chmod(self.file_path, 0o777)
            stream.write(data)

    def _render(self, template_dir, template_name):
        LOG.debug("Rendering {} file from {}.".format(template_name,
                                                      template_dir))
        template_environment = Environment(
            autoescape=False,
            loader=FileSystemLoader(template_dir),
            trim_blocks=False)

        rendered_file = template_environment.get_template(
            template_name).render(self.variables)
        return rendered_file

    def upload(self):
        self._create_file()
        cmd = get_kubectl_command()
        LOG.debug("Uploading configMap: {}".format(self.name))
        cmd.extend(["create", "configmap", self.name])
        cmd.extend(["--from-file", self.file_path])
        subprocess.call(cmd)

    def remove(self):
        cmd = get_kubectl_command()
        LOG.debug("Removing configMap: {}".format(self.name))
        cmd.extend(["delete", "configmap", self.name])
        subprocess.call(cmd)
