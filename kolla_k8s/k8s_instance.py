import subprocess
import os
import yaml
from oslo_config import cfg
from oslo_log import log as logging

from kolla_k8s.manifest import Manifest
from kolla_k8s.configmap import ConfigMap


LOG = logging.getLogger()
CONF = cfg.CONF
CONF.import_group('stackanetes', 'kolla_k8s.config.stackanetes')


class K8sInstance():
    def __init__(self, service_name, service_dir):
        LOG.debug("Creaeting instance: {}".format(service_name))
        self.service_name = service_name
        self.service_type = service_name.split("-")[0]
        self.service_dir = service_dir
        self._load_service_variables()
        self._load_configmaps()

    def _load_service_variables(self):
        variables = dict()
        path_to_service_conf = os.path.join(self.service_dir, '..',
                                            'stackanetes-services',
                                            self.service_type,
                                            self.service_name + '.yml')
        LOG.debug("Instance: {} loading files from {}".format(
            self.service_name, path_to_service_conf))
        with open(path_to_service_conf, 'r') as file:
            variables.update(yaml.load(file))
        self.configs = variables
        self.files = variables.get('files', [])

    def _load_configmaps(self):
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
        cmd = self._get_kubectl_command()

        cmd.extend([cmd_type, "-f", self.file_path])
        LOG.debug('{} instance {}'.format(cmd_type, self.service_name))
        subprocess.call(cmd)

    @staticmethod
    def _get_kubectl_command():
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
        return cmd
