#!/usr/bin/env python

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

import contextlib
import datetime
import fcntl
import filecmp
import json
import logging
import math
import os
import pwd
import re
import socket
import struct
import subprocess
import sys
import tempfile
import time

import jinja2
from jinja2 import meta
from kazoo import client as zk_client
from kazoo import exceptions as kz_exceptions
from kazoo.recipe import party
import six
from six.moves import queue

CMD_WAIT = 'waiting'
CMD_RUN = 'running'
CMD_ERR = 'error'
CMD_RETRY = 'retry'
CMD_DONE = 'done'

ZK_HOSTS = None
ROLE = None
PRIVATE_INTERFACE = None
PUBLIC_INTERFACE = None
ANSIBLE_PRIVATE = None
ANSIBLE_PUBLIC = None
DEPLOYMENT_ID = None
DEPLOYMENT = None
SERVICE = None
SERVICE_NAME = None
COPY_ALWAYS = None


if six.PY3:
    @contextlib.contextmanager
    def nested(*contexts):
        with contextlib.ExitStack() as stack:
            yield [stack.enter_context(c) for c in contexts]
else:
    nested = contextlib.nested


# zookeeper nodes
# SERVICE_NAME example is "openstack/nova/nova-compute"
#
# <root>/<dep_id>                   : DEPLOYMENT
# <root>/<dep_id>/<SERVICE_NAME>    : SERVICE
# SERVICE                           : service definition
# SERVICE/.party                    : dynamic service Party
# SERVICE/files/<file>              : file to place on the filesystem
# <root>/<dep_id>/variables/<option>: global config values
# SERVICE/variables/<option>        : per service config TODO(asalkeld)
# SERVICE/variables/<host>/<option> : per host config TODO(asalkeld)
# SERVICE/status/<cmd>/.done        : task complete


def set_globals():
    """Setup the globals from the environment."""
    global ZK_HOSTS, ROLE, PRIVATE_INTERFACE, PUBLIC_INTERFACE
    global ANSIBLE_PRIVATE, ANSIBLE_PUBLIC, DEPLOYMENT_ID, DEPLOYMENT
    global SERVICE, SERVICE_NAME, COPY_ALWAYS
    ZK_HOSTS = os.environ.get('KOLLA_ZK_HOSTS')
    PRIVATE_INTERFACE = os.environ.get('KOLLA_PRIVATE_INTERFACE', 'undefined')
    PUBLIC_INTERFACE = os.environ.get('KOLLA_PUBLIC_INTERFACE', 'undefined')
    strategy = os.environ.get('KOLLA_CONFIG_STRATEGY',
                              'COPY_ALWAYS')
    if strategy not in ('COPY_ALWAYS', 'COPY_ONCE'):
        LOG.error('Unknown KOLLA_CONFIG_STRATEGY %s,'
                  ' defaulting to COPY_ALWAYS', strategy)
        strategy = 'COPY_ALWAYS'
    COPY_ALWAYS = strategy == 'COPY_ALWAYS'
    system_prefix = os.environ.get('KOLLA_SYSTEM_PREFIX', '/kolla')
    app_id = os.environ['ZK_APP_ID']

    # All these are derived
    ANSIBLE_PRIVATE = 'ansible_%s' % PRIVATE_INTERFACE
    ANSIBLE_PUBLIC = 'ansible_%s' % PUBLIC_INTERFACE

    app_split = app_id.split('/')
    DEPLOYMENT_ID = app_split[1]
    DEPLOYMENT = os.path.join(system_prefix, DEPLOYMENT_ID)
    SERVICE = os.path.join(DEPLOYMENT, '/'.join(app_split[2:]))
    SERVICE_NAME = '/'.join(app_split[2:])
    # TODO(asalkeld) remove the concept of role
    ROLE = app_split[-1]


logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s')
LOG = logging.getLogger(__file__)


def set_loglevel():
    ll = os.environ.get('KOLLA_LOGLEVEL', 'info')
    try:
        nll = getattr(logging, ll.upper(), None)
    except ValueError:
        LOG.exception('Invalid log level: %s' % ll)
        nll = logging.INFO

    if not isinstance(nll, int):
        LOG.error('Invalid log level: %s' % ll)
        nll = logging.INFO
    LOG.setLevel(nll)

set_loglevel()


def get_hostname():
    return socket.gethostname()


def jinja_filter_bool(text):
    if not text:
        return False
    if text.lower() in ('true', 'yes'):
        return True
    return False


def jinja_regex_replace(value='', pattern='',
                        replacement='', ignorecase=False):
    if not isinstance(value, basestring):
        value = str(value)

    if ignorecase:
        flags = re.I
    else:
        flags = 0
    _re = re.compile(pattern, flags=flags)
    return _re.sub(replacement, value)


def jinja_render(content, global_config, name='dafault_name', extra=None):
    variables = global_config
    if extra:
        variables.update(extra)

    myenv = jinja2.Environment(loader=jinja2.DictLoader({name: content}))
    myenv.filters['bool'] = jinja_filter_bool
    myenv.filters['regex_replace'] = jinja_regex_replace
    return myenv.get_template(name).render(variables)


def jinja_find_required_variables(content, name='default_name'):
    myenv = jinja2.Environment(loader=jinja2.DictLoader({name: content}))
    myenv.filters['bool'] = jinja_filter_bool
    myenv.filters['regex_replace'] = jinja_regex_replace
    template_source = myenv.loader.get_source(myenv, name)[0]
    parsed_content = myenv.parse(template_source)
    return meta.find_undeclared_variables(parsed_content)


@contextlib.contextmanager
def zk_connection(zk_hosts):
    zk = zk_client.KazooClient(hosts=zk_hosts)
    try:
        zk.start()
        yield zk
    finally:
        zk.stop()


class TemplateFunctions(object):

    def __init__(self, zk):
        self._zk = zk

    def get_ip_address(self, ifname=PUBLIC_INTERFACE):
        if not ifname:
            ifname = PUBLIC_INTERFACE
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = str(socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            str(struct.pack('256s', ifname[:15].encode('utf-8')))
        )[20:24]))

        return address

    def list_ips_by_service(self, name, port=None, separator=',', prefix=None):
        """Converts a service to list of IP addresses

        Port, prefix and separator args are optional.
        openstack/nova/nova-compute 1234 -> 1.1.1.1:1234,1.1.1.2:1234
        """
        port = ':' + str(port) if port else ''
        prefix = str(prefix) if prefix else ''
        g_path = os.path.join(DEPLOYMENT, name, '.party')
        ips = []
        for host_data in party.Party(self._zk, g_path):
            data = json.loads(host_data)
            ansible_interface = filter(lambda x: "ansible_" in x and
                                                 "ansible_hostname" not in x,
                                       data.keys())
            ips.append(data[ansible_interface[0]]['ipv4']['address'])
        return separator.join([prefix + ip + port for ip in sorted(ips)])

    def _get_parties(self, node=None):
        if node is None:
            node = DEPLOYMENT

        if node.endswith('.party'):
            yield node
        try:
            children = self._zk.get_children(node)
        except kz_exceptions.NoNodeError:
            return

        for child in children:
            for p in self._get_parties(node=os.path.join(node, child)):
                yield p

    def get_groups_and_hostvars(self):
        # DEPRECATED
        # this returns an odd structure but it so we can re-use the
        # ansible templates.
        hostvars = {}
        groups = {}
        for p_path in self._get_parties():
            role = p_path.split('/')[-2]
            groups[role] = []
            group_unsorted = []
            for host_data in party.Party(self._zk, p_path):
                data = json.loads(host_data)
                ansible_interface = filter(lambda x: "ansible_" in x and
                                                     "ansible_hostname" not in x,
                                           data.keys())
                host = data[ansible_interface[0]]['ipv4']['address']
                group_unsorted.append(host)
                hostvars[host] = data
            groups[role] = sorted(group_unsorted)

        return groups, hostvars


def register_group_and_hostvars(zk):
    tf = TemplateFunctions(zk)
    addr = tf.get_ip_address(PUBLIC_INTERFACE)
    path = os.path.join(SERVICE, '.party')
    zk.retry(zk.ensure_path, path)

    data = {ANSIBLE_PUBLIC: {'ipv4': {'address':
                                      tf.get_ip_address(PUBLIC_INTERFACE)}},
            ANSIBLE_PRIVATE: {'ipv4': {'address':
                                       tf.get_ip_address(PRIVATE_INTERFACE)}},
            'ansible_hostname': get_hostname(),
            'api_interface': PUBLIC_INTERFACE}

    LOG.info('%s joining the %s party', addr, SERVICE_NAME)
    party.Party(zk, path, json.dumps(data)).join()


def write_file(conf, data):
    """Write the data to the file specified in the conf.

    If there is an existing file in the destination, compare the new
    contents with the existing contents. Return True if there is a difference.
    """
    owner = conf.get('owner')
    # Check for user and group id in the environment.
    try:
        uid = pwd.getpwnam(owner).pw_uid
    except KeyError:
        LOG.error('The specified user does not exist: {}'.format(owner))
        sys.exit(1)
    try:
        gid = pwd.getpwnam(owner).pw_gid
    except KeyError:
        LOG.error('The specified group does not exist: {}'.format(owner))
        sys.exit(1)

    dest = conf.get('dest')
    perm = int(conf.get('perm', 0))
    with tempfile.NamedTemporaryFile(prefix='kolla-mesos',
                                     delete=False) as tf:
        tf.write(data.encode('utf-8'))
        tf.flush()
        tf_name = tf.name

    if os.path.exists(dest) and filecmp.cmp(tf_name, dest, shallow=False):
        LOG.debug('write_file: %s not changed', dest)
        return False
    try:
        inst_cmd = ' '.join(['sudo', 'install', '-v',
                             '--no-target-directory',
                             '--group=%s' % gid, '--mode=%s' % perm,
                             '--owner=%s' % uid, tf_name, dest])
        subprocess.check_call(inst_cmd, shell=True)
    except subprocess.CalledProcessError as exc:
        LOG.error(exc)
        LOG.exception(inst_cmd)
    return True


def generate_host_vars(zk):
    # Note the following are DEPRECATED
    # hostvars, groups, inventory_hostname, ansible_hostname
    tf = TemplateFunctions(zk)
    host = tf.get_ip_address(PRIVATE_INTERFACE)
    groups, hostvars = tf.get_groups_and_hostvars()
    variables = {'hostvars': hostvars, 'groups': groups,
                 'inventory_hostname': host,
                 'ansible_hostname': host,
                 'get_hostname': get_hostname,
                 'get_ip_address': tf.get_ip_address,
                 'list_ips_by_service': tf.list_ips_by_service,
                 'deployment_id': DEPLOYMENT_ID,
                 'service_name': SERVICE_NAME}
    return variables


def render_template(zk, templ, variables, var_names):
    for var in var_names:
        if var not in variables:
            try:
                value, stat = zk.get(os.path.join(DEPLOYMENT,
                                     'variables', var))
                if stat.dataLength == 0:
                    value = ''
                    LOG.warning('missing required variable value %s', var)
            except kz_exceptions.NoNodeError:
                value = ''.encode('utf-8')
                LOG.error('missing required variable %s', var)

            variables[var] = value.decode('utf-8')
    #print "templ = {}".format(templ)
    #print "variables = {}".format(variables)
    return jinja_render(templ, variables)


def generate_main_config(zk, conf):
    """Take the app main config and render it if needed"""

    variables = generate_host_vars(zk)
    templ = conf.encode('utf-8')
    var_names = jinja_find_required_variables(templ)
    if not var_names:
        # not a template, doesn't need rendering.
        return json.loads(conf)

    content = render_template(zk, templ, variables, var_names)
    return json.loads(content)


class Command(object):
    def __init__(self, name, cmd, zk):
        self.raw_conf = cmd
        self.name = name
        self.zk = zk
        self.command = cmd['command']
        self.run_once = cmd.get('run_once', False)
        self.daemon = cmd.get('daemon', False)
        self.check_paths = [
            '%s/status/global/%s/%s' % (DEPLOYMENT, ROLE, self.name),
            '%s/status/%s/%s/%s' % (DEPLOYMENT, socket.gethostname(), ROLE,
                                    self.name)
        ]
        self.requires = self.get_requirements(cmd)
        self.init_path = os.path.dirname(self.check_paths[0])
        self.proc = None
        self.retries = int(cmd.get('retries', 0))
        if self.daemon:
            self.timeout = -1
        else:
            self.timeout = 120  # for now...
        self.delay = int(cmd.get('delay', 5))
        self.env = os.environ.copy()
        for ek, ev in cmd.get('env', {}).items():
            # make sure they are strings
            self.env[ek] = str(ev)
        self.requirements_fulfilled()

    def get_requirements(self, cmd):
        requires = []
        for req in cmd.get('dependencies', []):
            path = req['path']
            scope = req.get('scope', 'global')
            if scope == 'global':
                requires.append('%s/status/global/%s' % (DEPLOYMENT, path))
            elif scope == 'local':
                requires.append('%s/status/%s/%s' % (DEPLOYMENT,
                                                     socket.gethostname(),
                                                     path))
        return requires

    def requirements_fulfilled(self):
        """get requirements status

        if the requirement ends in 'daemon', then a state of
        running means it is fulfilled.

        else, then a state of done means it is fulfilled.
        """
        fulfilled = True
        for req in self.requires:
            success = CMD_DONE
            if req.endswith('daemon'):
                success = CMD_RUN
            state = self.get_state(req)
            if state != success:
                LOG.warning('%s is waiting for %s, in state: %s'
                            % (self.name, req, state))
                fulfilled = False
        return fulfilled

    def set_state(self, state):
        for check_path in self.check_paths:
            self.zk.retry(self.zk.ensure_path, check_path)
            current_state, _ = self.zk.get(check_path)
            if current_state.decode('utf-8') != state:
                LOG.info('path: %s, changing state from %s to %s'
                         % (check_path, current_state, state))
                self.zk.set(check_path, state.encode('utf-8'))

    def get_state(self, path=None):
        if not path:
            path = self.check_paths[0]
        state = None
        if self.zk.exists(path):
            state, _ = self.zk.get(path)
        if not state:
            return None
        return state.decode('utf-8')

    def sleep(self, queue_size, retry=False):
        seconds = math.ceil(20 / (1.0 + queue_size))

        if retry:
            seconds = min(seconds, self.delay)
            LOG.info('Command %s failed, rescheduling, '
                     '%d retries left', self.name, self.retries)
        time.sleep(seconds)

    def __str__(self):
        def get_true_attrs():
            for attr in ['run_once', 'daemon', 'retries']:
                if getattr(self, attr):
                    yield attr

        extra = ', '.join(get_true_attrs())
        if extra:
            extra = ' (%s)' % extra
        return '%s%s "%s"' % (
            self.name, extra, self.command)

    def run(self):
        self.generate_configs()
        zk = self.zk
        result = 0
        LOG.info('** > Running %s', self.name)
        if self.run_once:
            locks = []
            for check_path in self.check_paths:
                lock_path = check_path + '/lock'
                lock_name = get_hostname()
                zk.retry(zk.ensure_path, lock_path)
                lock = zk.Lock(lock_path, lock_name)
                LOG.info("Acquiring lock '%s'", lock_path)
                locks.append(lock)
            with nested(*locks):
                # We only interested in "global" path right now, since this
                # commands need to be run only once(per deploy)
                check_path = self.check_paths[0]
                state = self.get_state(check_path)
                if state == CMD_DONE:
                    LOG.info("Path '%s' exists: skipping command", check_path)
                    # Set state to ensure the local and global states are
                    # consistent.
                    self.set_state(CMD_DONE)
                else:
                    LOG.info("Path '%s' does not exist: running command",
                             check_path)
                    result = self._run_command()
            for check_path in self.check_paths:
                lock_path = check_path + '/lock'
                LOG.info("Released lock '%s'", lock_path)
        else:
            result = self._run_command()
        LOG.info('** < Complete %s result: %s', self.name, result)
        return result

    def generate_configs(self):
        """Render and create all config files for this command."""
        changes = False
        if 'files' not in self.raw_conf:
            return changes

        variables = generate_host_vars(self.zk)
        for name, item in six.iteritems(self.raw_conf['files']):
            LOG.debug('Name is: %s, Item is: %s', name, item)
            if name == 'kolla_mesos_start.py':
                continue
            raw_content, stat = self.zk.get(os.path.join(SERVICE, 'files',
                                                         name))
            templ = raw_content.decode('utf-8')
            var_names = jinja_find_required_variables(templ, name)
            if not var_names:
                # not a template, doesn't need rendering.
                if write_file(item, templ):
                    changes = True
                continue

            content = render_template(self.zk, templ, variables, var_names)
            if write_file(item, content):
                changes = True
        return changes

    def _run_command(self):
        LOG.debug("Running command: %s", self.command)
        self.retries = self.retries - 1

        def start_process():
            self.proc = subprocess.Popen(self.command, shell=True,
                                         env=self.env)
            if self.proc is None:
                LOG.error("Command '%s' failed (proc=None)", self.name)
                self.set_state(CMD_ERR)
                return 1

        def poll(timeout=-1, sleep_secs=10):
            now = datetime.datetime.now()
            while((datetime.datetime.now() - now).seconds < timeout or
                  timeout < 0):
                ret = self.proc.poll()
                LOG.debug("Command %s poll ret='%s'", self.name, ret)
                yield ret
                time.sleep(sleep_secs)

        if not self.daemon:
            # daemons will be set to running a little later
            self.set_state(CMD_RUN)
        if start_process() == 1:
            return 1

        if self.timeout > 0:
            for ret in poll(timeout=self.timeout):
                if ret == 0:
                    self.set_state(CMD_DONE)
                    LOG.debug("Command '%s' marked as done", self.name)
                    return ret
                if ret is not None:
                    self.set_state(CMD_ERR)
                    LOG.error("Command '%s' failed, retval: %s"
                              % (self.name, ret))
                    return ret

            LOG.error("Command failed with timeout (%s seconds)", self.timeout)
            self.set_state(CMD_ERR)
            self.kill_process()

        if self.daemon:
            time.sleep(20)
            for ret in poll():
                if ret is None:
                    self.set_state(CMD_RUN)
                    if COPY_ALWAYS and self.generate_configs():
                        self.kill_process()
                        if start_process() == 1:
                            ret = 1
                if ret is not None:
                    LOG.error("Command %s exited with (ret=%s)",
                              self.name, ret)
                    self.set_state(CMD_ERR)
                    return ret

    def kill_process(self):
        self.proc.terminate()
        time.sleep(3)
        self.proc.kill()
        self.proc.wait()


def run_commands(zk, service_conf):
    LOG.info('run_commands')
    cmdq = queue.Queue()

    if 'commands' in service_conf:
        conf = service_conf['commands']
        for name, cmd in conf.items():
            cmdq.put(Command(name, cmd, zk))

    if 'service' in service_conf:
        service_conf['service']['daemon']['daemon'] = True
        cmdq.put(Command('daemon', service_conf['service']['daemon'], zk))

    while not cmdq.empty():
        cmd = cmdq.get()
        if cmd.daemon and not cmdq.empty():
            # run the daemon command last
            cmd.set_state(CMD_WAIT)
            cmdq.put(cmd)
            continue
        if cmd.requirements_fulfilled():
            if cmd.run() != 0:
                if cmd.retries > 0:
                    cmd.set_state(CMD_RETRY)
                    cmd.sleep(cmdq.qsize(), retry=True)
                    cmdq.put(cmd)
                else:
                    # command failed and no retries, so exit.
                    sys.exit(1)
        else:
            cmd.set_state(CMD_WAIT)
            cmd.sleep(cmdq.qsize())
            cmdq.put(cmd)


def main():
    set_globals()
    LOG.info('starting')
    with zk_connection(ZK_HOSTS) as zk:
        service_conf_raw, stat = zk.get(SERVICE)
        service_conf = json.loads(service_conf_raw.decode('utf-8'))

        # don't join a Party if this container is not running a daemon
        # process.
        if 'service' in service_conf:
            register_group_and_hostvars(zk)
            service_conf = generate_main_config(zk, service_conf_raw)
            LOG.debug('Rendered service config: %s', service_conf)

        run_commands(zk, service_conf)


if __name__ == '__main__':
    main()
