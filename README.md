# Stackanetes

## Overview

Stackanetes is an easy way to deploy OpenStack on Kubernetes. This includes the control plane (keystone, nova, etc) and a "nova compute" container that runs virtual machines (VMs) under a hypervisor.

Checkout the video overview:

[![Stackanetes Overview](https://img.youtube.com/vi/DPYJxYulxO4/0.jpg)](https://www.youtube.com/watch?v=DPYJxYulxO4)

## Requirements

-  Kubernetes 1.2 cluster with minimum 3 kubernetes minions/workers
  - see guides for [CoreOS Kubernetes](https://coreos.com/kubernetes/docs/latest/)

## Getting started

### Building Configuration

Ensure the following packages are installed on the workstation that controls the Kubernetes cluster: git, python2.7, pip, [kubectl](https://github.com/kubernetes/kubernetes/releases) v1.2+.

Clone this repo: `git clone https://github.com/stackanetes/stackanetes` and move into the kolla directory `cd stackanetes/kolla_k8s`.

Install all python dependencies from requirements.txt and generate the `etc/kolla-k8s` config directory.

```
sudo pip install ansible
pip install -r requirements.txt
python setup.py build && python setup.py install
sudo ./generate_config_file_sample.sh
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

Customize the ansible inventory as needed to list all of the kubernetes machines in the cluster:

```
cd ../ansible
```

```
cat inventory/inventory
[machine]
172.17.4.99 ansible_user=core
```

```
ansible-playbook -i inventory site.yml
```

Label kubernetes nodes as their roles:

Persistent data stored on separate node

```
kubectl label node minion1 app=persistent-control
```

Non-persistent data stored on separate node preferable more than 1 node

```
kubectl label node minion2 app=non-persistent-control
```

Compute node will run nova-compute, the VMs

```
kubectl label node minion3 app=compute
```

Deploy OpenStack services with the kolla-k8s tool the currently supported services include:

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

```
kolla-k8s --config-dir /etc/kolla-k8s/ run <<service_name>>
```

## Known issues

Please refer to [issues](https://github.com/stackanetes/stackanetes/issues)
