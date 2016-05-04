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

import json
import os.path

from kazoo import exceptions as kz_exceptions
from oslo_config import cfg
from oslo_log import log as logging
import yaml

from kolla_k8s.common import file_utils
from kolla_k8s.common import jinja_utils
from kolla_k8s import exception

LOG = logging.getLogger()
CONF = cfg.CONF
CONF.import_group('kolla', 'kolla_k8s.config.kolla')
CONF.import_group('kolla', 'kolla_k8s.config.zookeeper')


def write_variables_zookeeper(zk, variables, base_node=None, overwrite=True):
    if base_node is None:
        base_node = os.path.join('kolla', CONF.kolla.deployment_id)
    filter_out = ['groups', 'hostvars', 'kolla_config',
                  'inventory_hostname']
    for var in variables:
        if (var in filter_out):
            LOG.debug('Var "%s" with value "%s" is filtered out' %
                      (var, variables[var]))
            continue
        var_value = variables[var]
        if isinstance(variables[var], dict):
            var_value = json.dumps(variables[var])
        var_path = os.path.join(base_node, 'variables', var)
        if not overwrite and zk.exists(var_path):
            LOG.debug('NOT Updating "%s" node in zookeeper(overwrite=False).',
                      var_path)
            return
        zk.ensure_path(var_path)
        if var_value is None:
            var_value = ''
        zk.set(var_path, var_value.encode('utf-8'))
        LOG.debug('Updated "%s" node in zookeeper.' % var_path)


def write_common_config_to_zookeeper(config_dir, zk, jinja_vars,
                                     overwrite=True):
    # 1. At first write global tools to ZK. FIXME: Make it a common profile
    conf_path = os.path.join(config_dir, 'common',
                             'common_config.yml.j2')
    common_cfg = yaml.load(jinja_utils.jinja_render(conf_path, jinja_vars))
    common_node = os.path.join('kolla', 'common')
    for script in common_cfg:
        script_node = os.path.join(common_node, script)
        if not overwrite and zk.exists(script_node):
            LOG.debug('NOT Updating "%s" node in zookeeper(overwrite=False).',
                      script_node)
            continue

        zk.ensure_path(script_node)
        source_path = common_cfg[script]['source']
        src_file = source_path
        if not source_path.startswith('/'):
            src_file = file_utils.find_file(source_path)
        with open(src_file) as fp:
            content = fp.read()
        zk.set(script_node, content.encode('utf-8'))


def get_variables_from_zookeeper(zk, needed_variables):
    path = os.path.join('/kolla', CONF.kolla.deployment_id, 'variables')
    variables = {}
    for var in needed_variables:
        try:
            variables[str(var)], _stat = zk.get(os.path.join(path, var))
        except kz_exceptions.NoNodeError:
            raise exception.KollaNotFoundException(var, entity='variable')

    return variables


# def apply_deployment_vars(jvars):
#     """Applies the orchestration logic defined in globals.yml.
#
#     If multinode mode is enabled, then it uses the default constraints.
#     And depending on the 'autodetect_resources' option, it figures out
#     how many instances of the services should be scheduled.
#     If multinode mode is disabled, then it checks whether
#     'mesos_aio_hostname' option is defined. If it is, then the
#     constraints for the given host are defined. If not, the constraints
#     disappear.
#     """
#     multinode = type_utils.str_to_bool(jvars['multinode'])
#     if multinode:
#         autodetect_resources = type_utils.str_to_bool(
#             jvars['autodetect_resources'])
#         if autodetect_resources:
#             controller_nodes, compute_nodes, storage_nodes, all_nodes = \
#                 mesos_utils.get_number_of_nodes()
#         else:
#             try:
#                 controller_nodes = jvars['controller_nodes']
#                 compute_nodes = jvars['compute_nodes']
#                 storage_nodes = jvars['storage_nodes']
#             except KeyError:
#                 raise exception.UndefinedOption(
#                     'When "autodetect_resources" option is disabled, '
#                     '"controller_nodes", "compute_nodes" and'
#                     '"storage_nodes" have to be defined.')
#             all_nodes = controller_nodes + compute_nodes + storage_nodes
#     else:
#         controller_nodes = 1
#         compute_nodes = 1
#         storage_nodes = 1
#         all_nodes = 1
#         controller_constraints = ""
#         compute_constraints = ""
#         controller_compute_constraints = ""
#         storage_constraints = ""
#         mesos_aio_hostname = jvars.get('mesos_aio_hostname')
#         if mesos_aio_hostname is not None:
#             constraints = '[["hostname", "CLUSTER", "%s"]]' % \
#                 mesos_aio_hostname
#             controller_constraints = constraints
#             compute_constraints = constraints
#             controller_compute_constraints = constraints
#             storage_constraints = constraints
#         jvars.update({
#             'controller_constraints': controller_constraints,
#             'compute_constraints': compute_constraints,
#             'controller_compute_constraints':
#             controller_compute_constraints,
#             'storage_constraints': storage_constraints
#         }, force=True)
#     jvars.update({
#         'controller_nodes': str(controller_nodes),
#         'compute_nodes': str(compute_nodes),
#         'storage_nodes': str(storage_nodes),
#         'all_nodes': str(all_nodes)
#     }, force=True)


# def get_marathon_framework(jvars):
#     try:
#         mframework = jvars['marathon_framework']
#     except KeyError:
#         mframework = mesos_utils.get_marathon()
#         if mframework is not None:
#             jvars.update({'marathon_framework': mframework})
#         else:
#             raise exception.UndefinedOption(
#                 'Please define marathon_framework')
#     LOG.info('Marathon framework: %s' % mframework)
