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

import functools
import json
import os.path
import subprocess
import time

from jinja2 import Environment, FileSystemLoader
from oslo_config import cfg
from oslo_log import log as logging
from six.moves import configparser
from six.moves import cStringIO
import yaml

from kolla_k8s.common import file_utils
from kolla_k8s.common import jinja_utils
from kolla_k8s.common import zk_utils
from kolla_k8s import configuration as config
from kolla_k8s import service_definition

LOG = logging.getLogger()
CONF = cfg.CONF
CONF.import_group('k8s', 'kolla_k8s.config.k8s')
CONF.import_group('kolla', 'kolla_k8s.config.kolla')
CONF.import_group('service', 'kolla_k8s.config.service')


def execute_if_enabled(f):
    """Decorator for executing methods only if runner is enabled."""
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if not self._enabled:
            return
        return f(self, *args, **kwargs)
    return wrapper


class File(object):
    def __init__(self, conf, name, service_name):
        self._conf = conf
        self._name = name
        self._service_name = service_name
        self.base_dir = os.path.abspath(file_utils.find_base_dir())

    def merge_ini_files(self, source_files):
        config_p = configparser.ConfigParser()
        for src_file in source_files:
            if not src_file.startswith('/'):
                src_file = os.path.join(self.base_dir, src_file)
            if not os.path.exists(src_file):
                LOG.warning('path missing %s' % src_file)
                continue
            config_p.read(src_file)
        merged_f = cStringIO()
        config_p.write(merged_f)
        return merged_f.getvalue()

    def write_to_zookeeper(self, zk, base_node):
        dest_node = os.path.join(base_node, self._service_name,
                                 'files', self._name)
        zk.ensure_path(dest_node)
        if isinstance(self._conf['source'], list):
            content = self.merge_ini_files(self._conf['source'])
        else:
            src_file = self._conf['source']
            if not src_file.startswith('/'):
                src_file = file_utils.find_file(src_file)
            with open(src_file) as fp:
                content = fp.read()
        zk.set(dest_node, content.encode('utf-8'))


class Command(object):
    def __init__(self, conf, name, service_name):
        self._conf = conf
        self._name = name
        self._service_name = service_name

    def write_to_zookeeper(self, zk, base_node):
        for fn in self._conf.get('files', []):
            fo = File(self._conf['files'][fn], fn, self._service_name)
            fo.write_to_zookeeper(zk, base_node)


class Runner(object):
    def __init__(self, conf):
        self._conf = conf
        self.base_dir = os.path.abspath(file_utils.find_base_dir())
        self.type_name = None
        self._enabled = self._conf.get('enabled', True)
        if not self._enabled:
            LOG.warn('Service %s disabled', self._conf['name'])
        self.app_file = None
        self.app_def = None

    def __new__(cls, conf):
        """Create a new Runner of the appropriate class for its type."""
        # Call is already for a subclass, so pass it through
        RunnerClass = cls
        return super(Runner, cls).__new__(RunnerClass)

    @classmethod
    def load_from_file(cls, service_file, variables):
        return Runner(yaml.load(
                      jinja_utils.jinja_render(service_file, variables)))

    def _list_commands(self):
        if 'service' in self._conf:
            yield 'daemon', self._conf['service']['daemon']
        for key in self._conf.get('commands', []):
            yield key, self._conf['commands'][key]

    @execute_if_enabled
    def write_to_zookeeper(self, zk, base_node):
        for cmd_name, cmd_conf in self._list_commands():
            cmd = Command(cmd_conf, cmd_name, self._conf['name'])
            cmd.write_to_zookeeper(zk, base_node)

        dest_node = os.path.join(base_node, self._conf['name'])
        zk.ensure_path(dest_node)
        try:
            zk.set(dest_node, json.dumps(self._conf).encode('utf-8'))
        except Exception as te:
            LOG.error('%s=%s -> %s' % (dest_node, self._conf, te))

    @classmethod
    def load_from_zk(cls, zk, service_name):
        variables = _load_variables_from_zk(zk)
        base_node = os.path.join('kolla', CONF.kolla.deployment_id)
        dest_node = os.path.join(base_node, "openstack", service_name.split('-')[0], service_name)
        try:
            conf_raw, _st = zk.get(dest_node)
        except Exception as te:
            LOG.error('%s -> %s' % (dest_node, te))
            raise NameError(te)
        return Runner(yaml.load(
                      jinja_utils.jinja_render_str(conf_raw.decode('utf-8'),
                                                   variables)))


class JvarsDict(dict):
    """Dict which can contain the 'global_vars' which are always preserved.

    They cannot be be overriden by any update nor single item setting.
    """

    def __init__(self, *args, **kwargs):
        super(JvarsDict, self).__init__(*args, **kwargs)
        self.global_vars = {}

    def __setitem__(self, key, value, force=False):
        if not force and key in self.global_vars:
            return
        return super(JvarsDict, self).__setitem__(key, value)

    def set_force(self, key, value):
        """Sets the variable even if it will override a global variable."""
        return self.__setitem__(key, value, force=True)

    def update(self, other_dict, force=False):
        if not force:
            other_dict = {key: value for key, value in other_dict.items()
                          if key not in self.global_vars}
        super(JvarsDict, self).update(other_dict)

    def set_global_vars(self, global_vars):
        self.update(global_vars)
        self.global_vars = global_vars


def _load_variables_from_file(service_dir, project_name):
    config_dir = os.path.join(service_dir, '..', 'config')
    jvars = JvarsDict()
    with open(file_utils.find_config_file('globals.yml'), 'r') as gf:
        jvars.set_global_vars(yaml.load(gf))
    with open(file_utils.find_config_file('passwords.yml'), 'r') as gf:
        jvars.update(yaml.load(gf))
    # Apply the basic variables that aren't defined in any config file.
    jvars.update({
        'deployment_id': CONF.kolla.deployment_id,
        'node_config_directory': '',
        'timestamp': str(time.time())
    })
    # Get the exact marathon framework name.
    #config.get_marathon_framework(jvars)
    # all.yml file uses some its variables to template itself by jinja2,
    # so its raw content is used to template the file
    all_yml_name = os.path.join(config_dir, 'all.yml')
    jinja_utils.yaml_jinja_render(all_yml_name, jvars)
    # Apply the dynamic deployment variables.
    #config.apply_deployment_vars(jvars)

    proj_yml_name = os.path.join(config_dir, project_name,
                                 'defaults', 'main.yml')
    if os.path.exists(proj_yml_name):
        jinja_utils.yaml_jinja_render(proj_yml_name, jvars)
    else:
        LOG.warning('Path missing %s' % proj_yml_name)
    return jvars


def _build_runner(service_name, service_dir, variables=None):
    config_dir = os.path.join(service_dir, '..', 'config')
    base_node = os.path.join('kolla', CONF.kolla.deployment_id)
    filename = service_definition.find_service_file(service_name,
                                                    service_dir)
    proj_name = filename.split('/')[-2]

    # is this a snapshot or from original src?
    variables = _load_variables_from_file(service_dir, proj_name)

    # 1. validate the definition with the given variables
    service_definition.validate(service_name, service_dir, variables)
    runner = Runner.load_from_file(filename, variables)
    with zk_utils.connection() as zk:
        # 2. write variables to zk (globally)
        config.write_variables_zookeeper(zk, variables)
        # 3. write common config and start script
        config.write_common_config_to_zookeeper(config_dir, zk, variables)

        # 4. write files/config to zk
        runner.write_to_zookeeper(zk, base_node)


def _load_variables_from_zk(zk):
    path = os.path.join('/kolla', CONF.kolla.deployment_id, 'variables')
    variables = {}
    try:
        var_names = zk.get_children(path)
    except Exception:
        var_names = []
    for var in var_names:
        value, _stat = zk.get(os.path.join(path, var))
        variables[var] = value.decode('utf-8')
    # Add deployment_id
    variables.update({'deployment_id': CONF.kolla.deployment_id})
    # override node_config_directory to empty
    variables.update({'node_config_directory': ''})
    return variables


# Public API below
##################
def run_service(service_name, service_dir, variables=None):
    # generate zk variables
    if service_name == 'nova-compute':
        service_list = ['nova-compute', 'nova-libvirt', 'openvswitch-vswitchd',
                        'neutron-openvswitch-agent', 'openvswitch-db']
    elif service_name == 'network-node':
        service_list = ['neutron-openvswitch-agent', 'neutron-dhcp-agent',
                        'neutron-metadata-agent', 'openvswitch-vswitchd',
                        'openvswitch-db', 'neutron-l3-agent']
    #TODO: load this service _list from config
    elif service_name == 'all':
        service_list = ['keystone-init', 'keystone-api', 'keystone-db-sync',
                        'glance-init', 'mariadb', 'rabbitmq', 'glance-registry',
                        'glance-api', 'nova-init', 'nova-api', 'nova-scheduler',
                        'nova-conductor', 'nova-consoleauth', 'neutron-init',
                        'neutron-server', 'horizon', 'nova-compute',
                        'nova-libvirt', 'openvswitch-vswitchd',
                        'neutron-openvswitch-agent', 'openvswitch-db',
                        'neutron-dhcp-agent', 'neutron-metadata-agent',
                        'openvswitch-db', 'neutron-l3-agent', 'nova-novncproxy']
    elif service_name == 'zookeeper':
        service_list = []
    else:
        service_list = [service_name]
    for service in service_list:
        _build_runner(service, service_dir, variables=variables)
    _deploy_instance(service_name)


def kill_service(service_name):
    if service_name == "all":
        with zk_utils.connection() as zk:
            status_node = os.path.join('kolla', CONF.kolla.deployment_id,
                                       'status')
            zk.delete(status_node, recursive=True)
    _delete_instance(service_name)


def _get_mount_path(service_name):
    try:
        path = CONF.service.get(service_name.replace("-", "_") + "_mpath")
    except cfg.NoSuchOptError:
        return {}
    host_path, container_path = path.split(":")
    return {"host_path": host_path,
            "container_path": container_path}


def _get_external_ip(service_name):
    try:
        ip = CONF.service.get(service_name.replace("-", "_") + "_external_ip")
    except cfg.NoSuchOptError:
        return {}
    return {"external_ip": ip}


def _generate_generic_control(service_name):
    service_type = service_name.split("-")[0] if "-" in service_name else None
    variables = {
         "service_name": service_name,
         "service_type": service_type,
         "image_version": CONF.kolla.tag,
         "memory": CONF.service.memory,
         "ports": CONF.service.get(service_name.replace("-", "_") + "_ports"),
         "docker_registry": CONF.k8s.docker_registry,
         }
    variables.update(_get_mount_path(service_name))
    variables.update(_get_external_ip(service_name))

    template_environment = Environment(
        autoescape=False,
        loader=FileSystemLoader(CONF.k8s.yml_dir_path),
        trim_blocks=False)

    rendered_file = template_environment.get_template(
        "generic-control.yml.j2").render(variables)
    from tempfile import mkstemp
    _, file_path = mkstemp(suffix="generic")
    with open(os.path.join(file_path), 'w') as stream:
        try:
            stream.write(rendered_file)
            stream.close()
            return file_path
        except IOError:
            LOG.error("Cannot create file: {} ".format(file_path))


def _deploy_instance(service_name):
    cmd = [CONF.k8s.kubectl_path]
    if CONF.k8s.host:
        server = "--server=" + CONF.k8s.host
        cmd.append(server)
    if CONF.k8s.kubeconfig_path:
        kubeconfig_path = "--kubeconfig=" + CONF.k8s.kubeconfig_path
        cmd.append(kubeconfig_path)
    if CONF.k8s.context:
        context = "--context=" + CONF.k8s.context
        cmd.append(context)

    if service_name in CONF.service.control_services_list:
        file_path = _generate_generic_control(service_name)
        cmd.extend(["create", "-f", file_path])
        subprocess.call(cmd)
        os.remove(file_path)
        return

    service_path = os.path.join(CONF.k8s.yml_dir_path, service_name + ".yml")
    if service_name == 'all':
        service_path = os.path.join(CONF.k8s.yml_dir_path, "")

    cmd.extend(["create", "-f", service_path])
    subprocess.call(cmd)


def _delete_instance(service_name):
    cmd = [CONF.k8s.kubectl_path]
    if CONF.k8s.host:
        server = "--server=" + CONF.k8s.host
        cmd.append(server)
    if CONF.k8s.kubeconfig_path:
        kubeconfig_path = "--kubeconfig=" + CONF.k8s.kubeconfig_path
        cmd.append(kubeconfig_path)
    if CONF.k8s.context:
        context = "--context=" + CONF.k8s.context
        cmd.append(context)

    if service_name in CONF.service.control_services_list:
        file_path = _generate_generic_control(service_name)
        cmd.extend(["delete", "-f", file_path])
        subprocess.call(cmd)
        os.remove(file_path)
        return

    service_path = os.path.join(CONF.k8s.yml_dir_path, service_name + ".yml")
    if service_name == 'all':
        service_path = CONF.k8s.yml_dir_path

    cmd.extend(["delete", "-f", service_path])
    subprocess.call(cmd)
