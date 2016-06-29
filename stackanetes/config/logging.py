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

from oslo_config import cfg


CONF = cfg.CONF
logging_opts = [
    cfg.StrOpt('logging_default_format_string',
               default='%(levelname)s - %(message)s'),
    cfg.StrOpt('default_log_levels',
               default='dcos.http=ERROR,'
                       'dcos.util=ERROR,'
                       'kazoo.client=ERROR,'
                       'requests.packages.urllib3.connectionpool=ERROR')
]
CONF.register_opts(logging_opts)
