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

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger()
CONF = cfg.CONF
CONF.import_group('stackanetes', 'stackanetes.config.stackanetes')
CONF.import_group('ceph', 'stackanetes.config.ceph')
GENERIC_TYPES = ['job', 'deployment', 'daemonset']
CUSTOM_TYPES = ['fluentd-elasticsearch', 'rgw']
DEPENDENCY_PREFIX = "DEPENDENCY_"


class Manifest(object):
    def __init__(self, configuration, service_dir):
        self.service_dir = service_dir
        self.type = configuration['type']
        self.service_name = configuration['name']
        self.label = configuration.get('label', None)
        self.external_ip_enabled = configuration.get('external_ip_enabled',
                                                     False)
        self.replicas = configuration.get('replicas', CONF.stackanetes.replicas)
        self.memory = CONF.stackanetes.memory
        self.docker_registry = CONF.stackanetes.docker_registry
        self.image_version = CONF.stackanetes.docker_image_tag
        self.host_interface = CONF.stackanetes.minion_interface_name
        self.external_ip = CONF.stackanetes.external_ip
        self.image_prefix = CONF.stackanetes.image_prefix
        self.host_network = configuration.get('host_network', False)
        self.namespace = CONF.stackanetes.namespace
        self.annotations = configuration.get('annotations', {})
        self.ports = configuration.get('ports', [])
        self.host_ports = configuration.get('host_ports', [])
        for port in self.ports:
            if not port.get('target_port'):
                port['target_port'] = port.get('port')
        if configuration.get('containers'):
            self._parameters_for_multi_containers_pod(configuration)
        else:
            self._parameters_for_single_container_pod(configuration)
        self.template_name = self._find_template()

    def _parameters_for_single_container_pod(self, configuration):
        self.command = configuration.get('command')
        self.configmaps = configuration.get('files', [])
        self.image = configuration.get('image')
        self.envs = configuration.get('envs', [])
        self.privileged = configuration.get('privileged', True)
        self.session_affinity = configuration.get("session_affinity", [])
        self.non_root = configuration.get("non_root", [])
        self.emptydirs = configuration.get('emptyDirs', [])
        self.mounts = configuration.get('mounts', [])
        if self.command:
            self.envs.append({'COMMAND': self.command})
        self.template_name = self._find_template()
        self._set_service_type()
        if configuration.get('dependencies'):
            self._add_dependencies(self.envs, configuration['dependencies'])
        self._add_files_list(self.envs, self.configmaps)

    def _parameters_for_multi_containers_pod(self, configuration):
        config_maps = []
        empty_dirs = []
        mounts = []
        self.containers = []
        for container_conf in configuration['containers']:
            container_dict = {}
            container_dict['command'] = container_conf.get('command')
            container_dict['image'] = container_conf['image']
            container_dict['name'] = container_conf['name']
            container_dict['envs'] = container_conf.get('envs', [])
            container_dict['privileged'] = container_conf.get('privileged',
                                                              True)
            container_dict['emptydirs'] = container_conf.get('emptyDirs', [])
            container_dict['configmaps'] = container_conf.get('files', [])
            config_maps.extend(container_dict['configmaps'])
            container_dict['emptyDirs'] = container_conf.get('emptyDirs', [])
            empty_dirs.extend(container_dict['emptyDirs'])
            container_dict['mounts'] = container_conf.get('mounts', [])
            mounts.extend(container_dict['mounts'])
            if container_dict['command']:
                container_dict['envs'].append(
                    {'COMMAND': container_conf['command']})
            self.containers.append(container_dict)
            if configuration.get('dependencies'):
                self._add_dependencies(container_dict['envs'],
                                       configuration['dependencies'])
            if container_conf.get('dependencies'):
                self._add_container_dependecies(
                    container_dict['envs'], container_conf[
                        'dependencies'])
            self._add_files_list(container_dict['envs'],
                                 container_dict['configmaps'])

        self.configmaps = self._filter_elements(config_maps, 'configmap_name')
        self.emptydirs = self._filter_elements(empty_dirs, 'name')
        self.mounts = self._filter_elements(mounts, 'name')

    def _add_files_list(self, envs, configmaps):
        for config in configmaps:
            if 'dest_file_name' in config:
                config['key_name'] = config['dest_file_name']
            else:
                config['key_name'] = config['file_name']
        configmaps_string = ','.join(map(lambda x: '/'.join(
            [x['container_path'], x['key_name']]), configmaps))
        config_env_name = self._prepare_dependency_name("CONFIG")
        envs.append({config_env_name: configmaps_string})

    @staticmethod
    def _prepare_dependency_name(dependency_name):
        return ''.join([DEPENDENCY_PREFIX, dependency_name])

    def _add_dependencies(self, envs, dependencies):
        jobs = ','.join(dependencies.get('job', []))
        job_env_name = self._prepare_dependency_name("JOBS")
        envs.append({job_env_name: jobs})
        services = ','.join(dependencies.get('service', []))
        if CONF.ceph.ceph_enabled and self.service_name != 'rgw':
            services = ','.join([services, 'rgw'])
        service_env_name = self._prepare_dependency_name("SERVICE")
        envs.append({service_env_name: services})
        ds = ','.join(dependencies.get('ds', []))
        ds_env_name = self._prepare_dependency_name("DAEMONSET")
        envs.append({ds_env_name: ds})

    def _add_container_dependecies(self, envs, dependencies):
        containers = ','.join(dependencies.get('containers', []))
        container_env_name = self._prepare_dependency_name("CONTAINER")
        envs.append({container_env_name: containers})

    def render(self):
        LOG.debug("Start rendering manifest for {}".format(self.service_name))
        template_dir = os.path.join(self.service_dir, '..', 'templates')
        template_environment = Environment(
            autoescape=False,
            loader=FileSystemLoader(template_dir),
            trim_blocks=False)

        try:
            data = template_environment.get_template(self.template_name).render(
                self.__dict__)
        except TemplateSyntaxError as err:
            LOG.error("Cannot render manifest. Err={}".format(err))
            raise TemplateSyntaxError("Cannot render manifest")
        return data

    def _find_template(self):
        if self.type.count('/') != 1:
            msg = "Invalid format type of {} service. Service type should " \
                  "have following format (generic|job)/(template_name)."
            LOG.error(msg)
            raise KeyError(msg)
        template_type, template_name = self.type.split('/')
        if template_type == "generic" and template_name in GENERIC_TYPES:
            return "generic/{}.yml.j2".format(template_name)
        elif template_type == "custom" and template_name in CUSTOM_TYPES:
            return "custom/{}.yml.j2".format(template_name)
        else:
            msg = "{} type is not supported".format(self.type)
            LOG.error(msg)
            raise KeyError(msg)

    # TODO(DTadrzak): check if those method is still required
    def _set_service_type(self):
        self.service = self.service_name.split("-")[0]

    @staticmethod
    def _filter_elements(dict_list, key_name):
        filtered_list = []
        new_list = []
        for dictionary in dict_list:
            if dictionary[key_name] not in filtered_list:
                new_list.append(dictionary)
                filtered_list.append(dictionary[key_name])
        return new_list
