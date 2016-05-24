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
        self.command = configuration['command']
        self.configmaps = configuration['files']
        self.image = configuration.get('image')
        self.ports = configuration.get('ports', [])
        self.envs = configuration.get('envs', [])
        self.emptydirs = configuration.get('emptyDirs', [])
        self.envs.append({'COMMAND': self.command})
        self._get_files_list()
        if configuration.get('dependencies'):
            self._find_dependencies(configuration['dependencies'])
        self.external_ip = configuration.get('external_ip')
        self.template_name = self._find_template()
        self._set_service_type()
        self.memory = CONF.stackanetes.memory
        self.docker_registry = CONF.stackanetes.docker_registry
        self.image_version = CONF.stackanetes.docker_image_tag
        self.host_interface = CONF.stackanetes.minion_interface_name

    def _get_files_list(self):
        # TODO(DTadrzak): switch on after Piotr's fix
         self.configmaps_string = ','.join(map(lambda x: '/'.join(
             [x['container_path'], x['file_name']]), self.configmaps))

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

    def _set_service_type(self):
        self.service = self.service_name.split("-")[0]
