# Stackanetes

## Overview

Stackanetes is heavily based on kolla-mesos (project abandoned).
Link to base [kolla repo](https://github.com/openstack/kolla)

Stackanetes is an easy way to deploy OpenStack on Kubernetes. This includes the control plane (keystone, nova, etc) and a "nova compute" container that runs virtual machines (VMs) under a hypervisor.

***_This code is heavily experimental and should only be used for demo purposes. The architecture of this project will change significantly._***

Checkout the video overview:

[![Stackanetes Overview](https://img.youtube.com/vi/DPYJxYulxO4/0.jpg)](https://www.youtube.com/watch?v=DPYJxYulxO4)

## Requirements

-  Kubernetes 1.3 cluster with minimum 2 kubernetes minions/workers
  - see guides for [CoreOS Kubernetes](https://coreos.com/kubernetes/docs/latest/)
-  Operation system with systemd version<=225
## Getting started

### Building Configuration

Ensure the following packages are installed on the workstation that controls the Kubernetes cluster: git, python2.7, pip, [kubectl](https://github.com/kubernetes/kubernetes/releases) v1.3+.

Clone this repo: `git clone https://github.com/stackanetes/stackanetes` and move into the kolla directory `cd stackanetes`.

Install all python dependencies from requirements.txt and generate the `/etc/stackanetes` config directory.

```
pip install -r requirements.txt
python setup.py build && python setup.py install
sudo ./generate_config_file_sample.sh
```

Now, set the following variables in /etc/stackanetes/stackanetes.conf:

```
[stackanetes]
context = /home/core/context // Path to context file
host = localhost:8001 // k8s API, this can be easily be configured by using 'kubectl proxy'
kubectl_path = /opt/bin/kubectl // absolute path to kubectl binary
docker_image_tag = barcelona // tag for images
docker_registry = 192.168.0.1 // docker registry name
minion_interface_name = eno1 // set physical interface name of minions
dns_ip = 10.2.0.10 // ip of k8s dns
cluster_name = cluster.local // k8s dns domain
external_ip = 192.168.0.1 // external ip for services like horizon
memory = 4096Mi // specify amount memory
image-prefix = // specify image-prefixy if necessary
namespace = stackanetes // specify kubernetes namespace
```

### Label kubernetes nodes

Control plane (mariadb, rabbitmq, nova-api, etc) will be labeled as such:

```
kubectl label node minion1 openstack-control-plane=enabled
```

Compute node will run couple of daemonsets like (compute-node, openvswitch-node, dhcp and l3-agent):

```
kubectl label node minion2  openstack-compute-node=enabled
```

## Docker images
Stackanetes requires images based on Kolla (To be changed). Those images also need a special entrypoint. Entrypoint code can be found here:
```
https://github.com/stackanetes/kubernetes-entrypoint
```
You can also use images stored on quay.io/stackanetes.

## Deploy OpenStack services

You can run service one by one:

```
stackanetes run <name-of-service>
```

Or deploy all with manage_all/py script:

```
./manage_all.py run
```

To kill all of OpenStack services use the same script but with kill parameter:

```
./manage_all.py kill
```
## Deploy Stackanetes via stackanetes-deployer POD

You can either use pre-build stackanetes-deployer docker image:
- quay.io/stackanetes/stackanetes-deployer:barcelona

or build your own image by executing

```
docker build -t stackanetes-deployer .
```

To install Stackanetes vis stackanetes-deployer POD you still have to label your nodes.

in `stackanetes-deployer.yml` change environment variables to fit your need:
- IMAGE_VERSION
- HOST_INTERFACE
- DOCKER_REGISTRY
- DNS_IP
- CLUSTER_NAME
- EXTERNAL_IP
- NAMESPACE
- IMAGE_PREFIX

```
    env:
    - name: IMAGE_VERSION
      value: "barcelona" # tag for images
    - name: HOST_INTERFACE
      value: "eno2" # name of physical interface for compute node
    - name: DOCKER_REGISTRY
      value: "192.168.0.1" # docker registry name
    - name: DNS_IP
      value: "10.2.0.10" # ip of k8s dns
    - name: CLUSTER_NAME
      value:  "cluster.local" # k8s dns domain
    - name: EXTERNAL_IP
      value: "192.168.0.1" # external ip for services like horizon
    - name: NAMESPACE
      value: "stackanetes"
    - name: IMAGE_PREFIX
      value: "stackanetes-"
```

then run:
```
kubectl create -f stackanetes-deployer.yml
```
## Known issues

Please refer to [issues](https://github.com/stackanetes/stackanetes/issues)
