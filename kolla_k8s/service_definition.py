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


import os.path
import socket
import yaml

import jinja2
from oslo_log import log

from kolla_k8s.common import jinja_utils
from kolla_k8s import exception

CNF_FIELDS = ('source', 'dest', 'owner', 'perm')
CMD_FIELDS = ('run_once', 'dependencies', 'command', 'env',
              'delay', 'retries', 'files')
DEP_FIELDS = ('path', 'scope')
SCOPE_OPTS = ('global', 'local')
LOG = log.getLogger()


def find_service_file(service_name, service_dir):
    # let's be flexible with the input, to make life easy
    # for users.
    if not os.path.exists(service_dir):
        raise exception.KollaNotFoundException(service_dir,
                                               entity='service directory')

    short_name = service_name.split('/')[-1].replace('_ansible_tasks', '-init')
    for root, dirs, names in os.walk(service_dir):
        for name in names:
            if short_name in name:
                return os.path.join(root, name)

    raise exception.KollaNotFoundException(service_name,
                                           entity='service definition')


def inspect(service_name, service_dir):
    filename = find_service_file(service_name, service_dir)
    try:
        required_variables = set.union(
            jinja_utils.jinja_find_required_variables(filename))
    except jinja2.exceptions.TemplateNotFound:
        raise exception.KollaNotFoundException(filename,
                                               entity='service definition')
    return dict(required_variables=list(required_variables))


def validate(service_name, service_dir, variables=None, deps=None):
    if variables is None:
        variables = {}
    if deps is None:
        deps = {}

    filename = find_service_file(service_name, service_dir)
    try:
        cnf = yaml.load(jinja_utils.jinja_render(filename, variables))
    except jinja2.exceptions.TemplateNotFound:
        raise exception.KollaNotFoundException(filename,
                                               entity='service definition')

    def get_commands():
        for cmd in cnf.get('commands', {}):
            yield cmd, cnf['commands'][cmd]
        if 'service' in cnf:
            yield 'daemon', cnf['service']['daemon']

    LOG.debug('%s: file found at %s' % (cnf['name'], filename))
    for cmd, cmd_info in get_commands():
        _validate_command(filename, cmd, cmd_info, deps,
                          cnf['name'], service_dir)
    return deps


def _validate_config(filename, conf, service_dir):
    for file in conf:
        for key in conf[file]:
            assert key in CNF_FIELDS, '%s: %s not in %s' % (filename,
                                                            key, CNF_FIELDS)
        srcs = conf[file]['source']
        if isinstance(srcs, str):
            srcs = [srcs]
        for src in srcs:
            file_path = os.path.join(service_dir, '..', src)
            if not file_path.startswith('/etc'):
                assert os.path.exists(file_path), '%s missing' % file_path


def _validate_command(filename, cmd, cmd_info, deps,
                      service_name, service_dir):
    for key in cmd_info:
        assert key in CMD_FIELDS, '%s not in %s' % (key, CMD_FIELDS)

    _, group, role = service_name.split('/')
    regs = ['%s/%s' % (role, cmd),
            '%s/%s/%s' % (socket.gethostname(), role, cmd)]
    reqs = cmd_info.get('dependencies', [])
    for reg in regs:
        if reg not in deps:
            deps[reg] = {'waiters': {}}
        deps[reg]['registered_by'] = cmd
        deps[reg]['name'] = cmd
        deps[reg]['run_by'] = filename
    for req in reqs:
        for key in req:
            assert key in DEP_FIELDS, '%s: %s not in %s' % (filename,
                                                            key, DEP_FIELDS)
        scope = req.get('scope', 'global')
        assert scope in SCOPE_OPTS, '%s: %s not in %s' % (filename,
                                                          scope, SCOPE_OPTS)
        req_path = req['path']
        if scope == 'local':
            req_path = os.path.join(socket.gethostname(), req_path)
        if req_path not in deps:
            deps[req_path] = {'waiters': {}}
        for reg in regs:
            deps[req_path]['waiters'][cmd] = reg
    if 'files' in cmd_info:
        _validate_config(filename, cmd_info['files'], service_dir)
    LOG.debug('%s: command "%s" validated' % (service_name, cmd))
