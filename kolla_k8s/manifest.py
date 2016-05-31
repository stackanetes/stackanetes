import os

from jinja2 import Environment, FileSystemLoader
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger()
CONF = cfg.CONF
CONF.import_group('stackanetes', 'kolla_k8s.config.stackanetes')


class Manifest(object):
    def __init__(self, configuration, service_dir):
        self.service_dir = service_dir
        self.type = configuration['type']
        self.service_name = configuration['name']
        if configuration.get('dependencies'):
            self._find_dependencies(configuration['dependencies'])
        self.external_ip = configuration.get('external_ip')
        self.memory = CONF.stackanetes.memory
        self.docker_registry = CONF.stackanetes.docker_registry
        self.image_version = CONF.stackanetes.docker_image_tag
        self.host_interface = CONF.stackanetes.minion_interface_name
        if configuration.get('containers'):
            self._parameters_for_multi_containers_pod(configuration)
        else:
            self._parameters_for_singel_container_pod(configuration)
        self._get_files_list()
        self.template_name = self._find_template()

    def _parameters_for_singel_container_pod(self, configuration):
        self.command = configuration['command']
        self.configmaps = configuration['files']
        self.image = configuration.get('image')
        self.ports = configuration.get('ports', [])
        self.envs = configuration.get('envs', [])
        self.session_affinity = configuration.get("session_affinity",[])
        self.non_root = configuration.get("non_root",[])
        self.emptydirs = configuration.get('emptyDirs', [])
        self.envs.append({'COMMAND': self.command})
        self.template_name = self._find_template()
        self._set_service_type()

    def _parameters_for_multi_containers_pod(self, configuration):
        config_maps = []
        empty_dirs = []
        mounts = []
        self.containers = []
        for container_configuration in configuration:
            container_dict = {}
            container_dict['command'] = container_configuration['command']
            container_dict['image'] = container_configuration['image']
            container_dict['name'] = container_configuration['name']
            container_dict['envs'] = container_configuration.get('envs', [])
            container_dict['emptydirs'] = configuration.get('emptyDirs', [])
            container_dict['configmaps'] = configuration.get('files', [])
            config_maps.extend(container_dict['configmaps'])
            container_dict['emptyDirs'] = configuration.get('emptyDirs', [])
            empty_dirs.extend(container_dict['emptyDirs'])
            container_dict['mounts'] = configuration.get('mounts', [])
            empty_dirs.extend(container_dict['mounts'])
            container_dict['envs'].append({'COMMAND': self.command})
            self.containers.append(container_dict)
        self.configmaps = set(config_maps)
        self.emptydirs = set(empty_dirs)
        self.mounts = set(mounts)

    def _get_files_list(self):
        # TODO(DTadrzak): switch on after Piotr's fix
        for config in self.configmaps:
            if 'dest_file_name' in config:
                config['key_name'] = config['dest_file_name']
            else:
                config['key_name'] = config['file_name']

        self.configmaps_string = ','.join(map(lambda x: '/'.join(
             [x['container_path'], x['key_name']]), self.configmaps))

    def _find_dependencies(self, dependencies):
        self.job_dependencies = dependencies.get('job', [])
        self.service_dependencies = dependencies.get('service', [])
        self.ds_dependencies = dependencies.get('ds', [])

    def render(self):
        template_dir = os.path.join(self.service_dir, '..', 'templates')

        template_environment = Environment(
            autoescape=False,
            loader=FileSystemLoader(template_dir),
            trim_blocks=False)
        print template_dir
        data = template_environment.get_template(self.template_name).render(
            self.__dict__)
        return data

    def _find_template(self):
        if self.type == "network-node":
            return "generic-network-node.yml.j2"
        elif self.type == "compute-node":
            return "generic-compute-node.yml.j2"
        elif self.type == "job":
            return "generic-job.yml.j2"
        elif self.type == "deployment":
            return "generic-deployment.yml.j2"
        else:
            msg = "{} type is not supported".format(self.type)
            LOG.error(msg)
            raise KeyError(msg)

    # TODO(DTadrzak): check if those method is still required
    def _set_service_type(self):
        self.service = self.service_name.split("-")[0]
