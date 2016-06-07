#!/bin/python
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
