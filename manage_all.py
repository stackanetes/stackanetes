#!/usr/bin/python

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
import sys

SERVICE_PATH = "/usr/local/share/stackanetes/stackanetes-services"


def main():
    if len(sys.argv) not in [2, 3]:
        exit("Please provide a 'run' or 'kill' as a script parameter")
    if sys.argv[1] not in ['run', 'kill', 'restart']:
        exit("Invalid argument, please provide 'run' or 'kill'")

    service = '' if len(sys.argv) == 2 else sys.argv[2]
    services = load_all_services(service)
    arguments = ['kill', 'run'] if sys.argv[1] == 'restart' else [sys.argv[1]]
    for argument in arguments:
        manage_services(services, argument)


def load_all_services(service):
    services = []
    for _, _, file_name in os.walk(os.path.join(SERVICE_PATH, service)):
        services.extend(file_name)
    # Remove .yml from the of service name
    services = [service.replace('.yml', '') for service in services]

    return services


def manage_services(services, manage_type):
    cmd = ['stackanetes', manage_type]
    for service_name in services:
        subprocess.call(cmd + [service_name])

if __name__ == "__main__":
    main()
