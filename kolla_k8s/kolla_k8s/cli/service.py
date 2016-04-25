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

from cliff import command
from oslo_config import cfg
from oslo_log import log


from kolla_k8s import service

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class Run(command.Command):
    """Run a service."""

    def get_parser(self, prog_name):
        parser = super(Run, self).get_parser(prog_name)
        parser.add_argument('service')
        return parser

    def take_action(self, parsed_args):
        service.run_service(parsed_args.service,
                            CONF.service_dir)


class Kill(command.Command):
    """Kill a service."""

    def get_parser(self, prog_name):
        parser = super(Kill, self).get_parser(prog_name)
        parser.add_argument('service')
        return parser

    def take_action(self, parsed_args):
        service.kill_service(parsed_args.service)
