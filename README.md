# Stackanetes

## Overview

Stackanetes is heavily based on kolla-mesos (project abandoned).
Link to base [kolla repo](https://github.com/openstack/kolla)

Stackanetes is an easy way to deploy OpenStack on Kubernetes. This includes the control plane (keystone, nova, etc) and a "nova compute" container that runs virtual machines (VMs) under a hypervisor.

***_This code is heavily experimental and should only be used for demo purposes. The architecture of this project will change significantly._***

Checkout the video overview:

[![Stackanetes Overview](https://img.youtube.com/vi/DPYJxYulxO4/0.jpg)](https://www.youtube.com/watch?v=DPYJxYulxO4)

## Requirements

-  Kubernetes 1.2 cluster with minimum 2 kubernetes minions/workers
  - see guides for [CoreOS Kubernetes](https://coreos.com/kubernetes/docs/latest/)

## Getting started

### Building Configuration

Ensure the following packages are installed on the workstation that controls the Kubernetes cluster: git, python2.7, pip, [kubectl](https://github.com/kubernetes/kubernetes/releases) v1.2+.

Clone this repo: `git clone https://github.com/stackanetes/stackanetes` and move into the kolla directory `cd stackanetes`.

Install all python dependencies from requirements.txt and generate the `etc/kolla-k8s` config directory.

```
pip install -r requirements.txt
python setup.py build && python setup.py install
sudo ./generate_config_file_sample.sh
```

Now, set the following variables in /etc/kolla-k8s/kolla-k8s.conf:

```
[k8s]
host = localhost:8001 // k8s API, this can be easily be configured by using 'kubectl proxy'
kubectl_path = /opt/bin/kubectl // absolute path to kubectl binary
yml_dir_path = /var/lib/kolla-k8s/ // absolute path to dir with manifests
[kolla]
tag = 2.0.0 // check available versions on quay.io/stackanetes
deployment_id = root
[network]
host_interface = eno1 // set interface name of host
[service]
horizon_filebased_external_ip = 10.10.10.11 // set ip of your minion
[zookeeper]
host = 10.10.10.11:30000 // this will be the NodePort of the running zookeeper after you deploy it, per below
```

In /etc/kolla-k8s/globals.yml change `enable_horizon` to yes and set the name of host interface for compute-node and network node:
```
####################
Networking options
####################
network_interface: "eth0" // name of interface inside container                  
neutron_external_interface: "eno2" // name of physical interface

####################
OpenStack options
###################

enable_horizon: "yes"
```

### Label kubernetes nodes

Control plane (mariadb, zookeeper, rabbitmq) will be labeled as such:

```
kubectl label node minion1 app=controller
```

Compute node will run nova-compute, the VMs. Currently you need to dedicate the host to these:

```
kubectl label node minion2 app=compute
```

### Final host dependencies

There are a few temporary hacks in place to allow `nova-compute` run with full host privileges. 

On all machines you must create the directories `/var/lib/nova` and `/var/lib/libvirt`:

```
mkdir -p /var/lib/nova /var/lib/libvirt
```

Additionally, a resolv.conf located at /home/core/resolv.conf must exist on all nodes that you want to be hypervisor nodes.

```
$ cat /home/core/resolv.conf
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.200.0.50
options ndots:5
```

## Deploy OpenStack services

First you must deploy zookeeper:

```
kolla-k8s --config-dir /etc/kolla-k8s run zookeeper
```

Then you can run everything else:

```
kolla-k8s --config-dir /etc/kolla-k8s run all
```

If you run into errors, run with the --debug flag for additional information:
```
kolla-k8s --debug
```
## Deploy Stackanetes via stackanetes-deployer POD

To install Stackanetes vis stackanetes-deployer POD you still have to label your nodes
and finish `Final host dependencies` step.

in `stackanetes-deployer.yml` change `HOST_INTERFACE` environment variable:

```
    env:
    - name: HOST_INTERFACE
      value: "eno2" # name of physical interface for compute node

```

then run:
```
kubectl create -f stackanetes-deployer.yml
```
## Known issues

Please refer to [issues](https://github.com/stackanetes/stackanetes/issues)
