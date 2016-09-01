# Stackanetes

Stackanetes is an initiative to make operating OpenStack as simple as running any application on Kubernetes.
Stackanetes deploys standard OpenStack services into containers and uses Kubernetes’ robust application lifecycle management capabilities to deliver a single platform for companies to run OpenStack Infrastructure-as-a-Service (IaaS) and container workloads.

## Overview

### Services

Stackanetes sets up the following OpenStack components:
- Cinder (with external Ceph storage)
- Glance (with external Ceph storage or local filesystem)
- Horizon
- Keystone
- Neutron + Open vSwitch
- Nova
- Searchlight + Elasticsearch

In addition to these, a few other applications are deployed:
- MariaDB
- Memcached
- RabbitMQ
- RADOS Gateway
- Traefik

Services are divided and scheduled into two groups, except from few services that run everywhere (e.g. Open vSwitch agents):
- The control plane, which runs all the OpenStack APIs and every other supporting applications,
- The compute plane, which is dedicated to run Nova's virtual machines.

### Requirements

For Stackanetes to run, there is a single requirement:
- Kubernetes 1.3+
  - Two nodes available for scheduling,
  - Virtualization support for compute nodes,
  - Kubelet running with `--allow-privileged=true`,
  - Network connectivity between the containers across nodes (e.g. flanneld),
  - DNS add-on.

To deploy Stackanetes, a container runtime is needed (e.g. rkt).

To enable Cinder and live-migration, a working Ceph cluster is also required.

### High-availability & Networking

Thanks to Kubernetes' [deployments](http://kubernetes.io/docs/user-guide/deployments/), common OpenStack APIs can be made highly-available using a single parameter, called `replicas`.

Internal traffic (i.e. inside the Kubernetes cluster) is load-balanced natively using Kubernetes' [services](http://kubernetes.io/docs/user-guide/services/). When Ingress is enabled, external traffic (i.e. from outside of the Kubernetes cluster) to OpenStack is routed from any of the Kubernetes' node to an Traefik instance, which then selects the appropriate service and forward the requests accordingly. By leveraging Kubernetes' services and health checks, high-availability of the OpenStack endpoints is achieved transparently: a simple round-robin DNS that resolves to few Kubernetes' nodes is sufficient.

Data availability for Cinder and Glance depends on the storage backend being used.

## Getting started

### Prepare the environment

#### Kubernetes

To setup a Kubernetes cluster, the [CoreOS guides](https://coreos.com/kubernetes/docs/latest/) could be used.

Two nodes must be labelled for Stackanetes' usage:

    kubectl label node minion1 openstack-control-plane=enabled
    kubectl label node minion2 openstack-compute-node=enabled

#### DNS

If Ingress is enabled, the DNS environment should be configured to resolve the following names (modulo a custom Ingress host that may have been configured) to at least some Kubernetes' nodes:

    identity.openstack.cluster
    horizon.openstack.cluster
    image.openstack.cluster
    network.openstack.cluster
    volume.openstack.cluster
    compute.openstack.cluster
    novnc.compute.openstack.cluster
    search.openstack.cluster

#### Ceph

If Ceph is enabled, few users and pools must be created.
The user and pool names can be customized. Note down the keyrings, they will be used d

    ceph osd pool create volumes 128
    ceph osd pool create images 128
    ceph osd pool create vms 128
    ceph auth get-or-create client.cinder mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=volumes, allow rwx pool=vms, allow rx pool=images'
    ceph auth get-or-create client.glance mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=images'
    ceph auth get-or-create client.rgw osd 'allow rwx' mon 'allow rw'

### kpm

[kpm](https://github/coreos/kpm) is the package manager and command-line tool to deploy stackanetes
#### Install kpm
##### From Pypi

kpm is a python2 package and available on pypi
```
$ sudo pip install kpm --pre
````
##### From git
```
git clone https://github.com/coreos/kpm.git kpm
cd kpm
sudo make install
```
#### Customize and configure stackanetes
Get the default configuration:
```
kpm pull stackanetes/stackanetes -H https://beta.kpm.sh --dest ./stackanetes
cd stackanetes/stackanetes_stackanetes_0.1.1
```

Values to modify are in `parameters.yaml`

#### Deploy
To deploy stackanetes:
```
kpm deploy stackanetes/stackanetes --variables parameters.yaml --namespace openstack -H https://beta.kpm.sh
```

### Access

Once Stackanetes is entirely deployed, we can log in to Horizon or use the CLI directly.

If Ingress is enabled, Horizon may be accessed on http://horizon.openstack.cluster:30080/. Otherwise, it will be available on port 80 of any defined external IP. The default credentials are _admin_ / _password_.

The file [env_openstack.sh](env_openstack.sh) contains the default environment variables required to interact with OpenStack using the `openstack` client.

### Update

The `deploy` command is idempotent and performs only required actions. 
This command is used to upgrade stackanetes resources, update/modifiy a custom parameters:

```
kpm deploy stackanetes/stackanetes --variables parameters.yaml --namespace openstack -H https://beta.kpm.sh
```

## Limitations

Some features haven't been implemented yet in Stackanetes:
- MariaDB, Memcached, RabbitMQ, Elasticsearch are not deployed in a highly-available manner,
- Some OpenStack features are missing (see components list above),
- Compute services can't be ran using the rkt container runtime,
- SSL/TLS is not terminated.
