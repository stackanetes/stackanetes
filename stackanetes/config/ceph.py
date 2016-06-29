# Copyright 2016 Intel Corporation
#
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
ceph_opts = [
    cfg.ListOpt('ceph_mons', default=["192.168.10.1","10.91.10.2"]),
    cfg.StrOpt('ceph_admin_keyring', default='ASDA=='),
    cfg.BoolOpt('ceph_enabled', default=True),
]


ceph_opt_group = cfg.OptGroup(name='ceph', title="ceph")
CONF.register_group(ceph_opt_group)
CONF.register_cli_opts(ceph_opts, ceph_opt_group)
CONF.register_opts(ceph_opts, ceph_opt_group)
