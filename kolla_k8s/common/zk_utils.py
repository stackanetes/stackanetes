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
import logging
import os
import os.path

from kazoo import client
from kazoo import exceptions
from oslo_config import cfg

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_group('zookeeper', 'kolla_k8s.config.zookeeper')


def clean(zk, path='/kolla'):
    zk.delete(path, recursive=True)


def _list_all(path, zk):
    values = {}
    data, stat = zk.get(path)
    if stat.dataLength > 0:
        values[path] = data.decode('utf-8')
    try:
        children = zk.get_children(path)
    except exceptions.NoNodeError:
        children = []
    for child in children:
        cvalues = _list_all(os.path.join(path, child), zk)
        if cvalues is not None:
            values.update(cvalues)
    return values


def list_all(path):
    if path is None:
        path = '/'
    with connection() as zk:
        return _list_all(path, zk)


def get_one(path):
    with connection() as zk:
        data, stat = zk.get(path)
        return {path: data.decode('utf-8')}


def set_one(path, value):
    with connection() as zk:
        zk.set(path, value.encode('utf-8'))


@contextlib.contextmanager
def connection():
    zk = client.KazooClient(hosts=CONF.zookeeper.host)
    try:
        zk.start()
        yield zk
    finally:
        zk.stop()
