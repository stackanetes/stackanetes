
# Stackanetes


## Overview

This project aims to create an easy way to deploy OpenStack on Kubernetes. In order to achieve that first version of Stackanetes is heavily based on [Kolla-Mesos](https://github.com/openstack/kolla-mesos) project.

## Requirements

 -  Kubernetes 1.2 cluster with minimum 3 kubernetes minions/workers
 - [SkyDNS](https://github.com/kubernetes/kubernetes/tree/master/cluster/addons/dns) addon installed

## Getting started

### Building Configuration 

Make sure following packages are installed on the system building the configuration: git, python2.7, pip, [kubectl](https://github.com/kubernetes/kubernetes/releases) v1.2+.

Clone this repo: `git clone https://github.com/stackanetes/stackanetes` and move into the kolla directory `cd stackanetes/kolla_k8s`.

Install all python dependencies from requirements.txt and generate the `etc/kolla-k8s` config directory.

```
pip install -r requirements.txt
./generate_config_file_sample.sh
```

Now, set the following variables in /etc/kolla-k8s/kolla-k8s.conf:
```
[k8s]
host = 10.10.10.10:8080 // k8s API
kubectl_path = /opt/bin/kubectl // absolute path to kubectl binary
yml_dir_path = /var/lib/kolla-k8s/ // absolute path to dir with manifests
[zookeeper]
host = 10.10.10.11:30000 //zookeeper address
```

- Run ansible role to generate rc files.
- Prepare ansible/groups_vars/all.yml:

```
dest_yml_file_dir: /var/lib/kolla-k8s //absolute path to dir with manifests
docker_registry: quay.io/stackanetes
host_interface: eno1 // name of interface for nova-compute in hostNetwork mode
image_version: 2.0.0 // check current version on quay.io/stackanetes
```

-  Run  ```ansible-playbook -i inventory site.yml```
- Build and install kolla_k8s: ```python setup.py build && python setup.py install```
- Label kubernetes nodes as  :
- ```kubectl label node minion1 app=persistent-control ``` // Persistent data stored on separate node
- ```kubectl label node minion2 app=non-persistent-control ``` // Non-persistent data stored on separate node preferable more than 1 node
- ```kubectl label node minion3 app=compute ``` // Compute node
- Deploy openstack service via kolla-k8s: ```kolla_k8s --config-dir /etc/kolla-k8s/ run <<service_name>>```

## Currently supported services
Persistent control:
 - zookeeper
 - mariadb
 - rabbitmq
 - glance
  - glance-init
  - glance-api
  - glance-registry

Non-persistent control:
 - keystone
  - keystone-init
  - keystone-db-sync
  - keystone-api
 - nova
  - nova-init
  - nova-api
  - nova-conductor
  - nova-consoleauth
  - nova-scheduler
  - nova-novncproxy
 - neutron
  - neutron-init
  - neutron-server
 - network-node // As a k8s daemon-set

Compute:
 - nova-compute // As a k8s daemon-set

## Known issues
Please refer to [issues](https://github.com/stackanetes/stackanetes/issues)
