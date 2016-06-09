#!/bin/python

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

import os
import subprocess

service_path = "/usr/local/share/stackanetes/stackanetes-services"

services_names = []

for _, _, files_names in os.walk(service_path):
    services_names.extend(files_names)

services_names = [ file_name[:-4] for file_name in services_names]

for service_name in services_names:
    cmd = ['stackanetes', '--config-dir', '/etc/stackanetes', '--debug', 'kill']
    cmd.append(service_name)
    subprocess.call(cmd)
for service_name in services_names:
    cmd = ['stackanetes', '--config-dir', '/etc/stackanetes', '--debug', 'run']
    cmd.append(service_name)
    subprocess.call(cmd)
