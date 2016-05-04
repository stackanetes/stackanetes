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

import collections
import os
from six.moves.urllib import parse


def env(*args, **kwargs):
    for arg in args:
        value = os.environ.get(arg)
        if value:
            return value
    return kwargs.get('default', '')


def dict_update(d, u):
    """Recursively update 'd' with 'u' and return the result."""

    if not isinstance(u, collections.Mapping):
        return u

    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = dict_update(d.get(k, {}), v)
        else:
            d[k] = u[k]
    return d


def get_query_string(search_opts):
    if search_opts:
        qparams = sorted(search_opts.items(), key=lambda x: x[0])
        query_string = "?%s" % parse.urlencode(qparams, doseq=True)
    else:
        query_string = ""
    return query_string
