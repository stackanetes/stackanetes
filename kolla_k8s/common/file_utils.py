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

import errno
import logging
import os
import platform
import sys

from oslo_utils import importutils

from kolla_k8s import exception

LOG = logging.getLogger(__name__)


def find_os_type():
    return platform.linux_distribution()[0]


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_src_dir():
    kolla_mesos = importutils.import_module('kolla_k8s')
    mod_path = os.path.abspath(kolla_mesos.__file__)
    # remove the file and module to get to the base.
    return os.path.dirname(os.path.dirname(mod_path))


def find_base_dir():
    script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    base_script_path = os.path.basename(script_path)
    if base_script_path == 'kolla-k8s':
        return script_path
    if base_script_path == 'kolla_k8s':
        return os.path.join(script_path, '..')
    if base_script_path == 'cmd':
        return os.path.join(script_path, '..', '..')
    if base_script_path == 'subunit':
        return get_src_dir()
    if base_script_path == 'bin':
        if find_os_type() in ['Ubuntu', 'debian']:
            base_dir = '/usr/local/share/kolla-k8s'
        else:
            base_dir = '/usr/share/kolla-k8s'

        if os.path.exists(base_dir):
            return base_dir
        else:
            return get_src_dir()
    return '/usr/share/kolla-k8s'


def find_config_file(filename):
    filepath = os.path.join('/etc/kolla-k8s', filename)
    if os.access(filepath, os.R_OK):
        config_file = filepath
    else:
        config_file = os.path.join(find_base_dir(),
                                   'etc', filename)
    return config_file


POSSIBLE_PATHS = set([
    '/usr/share/kolla-k8s',
    get_src_dir(),
    find_base_dir()
])


def find_file(filename):
    for path in POSSIBLE_PATHS:
        file_path = os.path.join(path, filename)
        if os.path.exists(file_path):
            return file_path
    raise exception.KollaNotFoundException(filename, entity='file')
