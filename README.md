# Stackanetes

Stackanetes is an initiative to make operating OpenStack as simple as running any application on Kubernetes.
Stackanetes deploys standard OpenStack services into containers and uses Kubernetes’ robust application lifecycle management capabilities to deliver a single platform for companies to run OpenStack Infrastructure-as-a-Service (IaaS) and container workloads.

## Overview

### Services

Stackanetes sets up the following OpenStack components:
- Cinder
- Glance
- Horizon
- Keystone
- Neutron
- Nova
- Searchlight

In addition to these, a few other applications are deployed:
- MariaDB
- Memcached
- RabbitMQ
- RADOS Gateway
- Traefik
- Elasticsearch
- Open vSwitch

Services are divided and scheduled into two groups, with the exception of the Open vSwitch agents which run everywhere:
- The control plane, which runs all the OpenStack APIs and every other supporting applications,
- The compute plane, which is dedicated to run Nova's virtual machines.

### Gotta go fast

Leaving aside the configuration of the [requirements], Stackanetes can fully deploy OpenStack from scratch in ~5-8min. But that's not the only strength of Stackanetes, its true power resides in its ability to help managing OpenStack's lifecycle.

[requirements]: #requirements

### Requirements

Stackanetes requires Kubernetes 1.3+ with:
  - At least two schedulable nodes,
  - At least one virtualization-ready node,
  - [Overlay network] & [DNS add-on],
  - Kubelet running with `--allow-privileged=true`,

While Glance may operate with local storage, a Ceph cluster is needed for Cinder. Nova's live-migration feature requires proper DNS resolution of the Kubernetes nodes' hostnames.

The [rkt] engine can be used in place of the default runtime with Kubernetes 1.4+ and rkt 1.14+. Note however that a known issue about mount propagation flags may prevent the Kubernetes' service account secret from being mounted properly on the Nova's libvirt pod, causing it to fail at startup.

[Overlay network]: http://kubernetes.io/docs/admin/networking/
[DNS add-on]: https://github.com/kubernetes/kubernetes/tree/master/cluster/addons/dns
[rkt]: https://github.com/coreos/rkt
[known issue]: https://github.com/coreos/rkt/issues/3228#issuecomment-249320705

### High-availability & Networking

Thanks to Kubernetes' [deployments](http://kubernetes.io/docs/user-guide/deployments/), OpenStack APIs can be made highly-available using a single parameter, called `deployment.replicas`.

Internal traffic (i.e. inside the Kubernetes cluster) is load-balanced natively using Kubernetes' [services]. When Ingress is enabled, external traffic (i.e. from outside of the Kubernetes cluster) to OpenStack is routed from any of the Kubernetes' node to an Traefik instance, which then selects the appropriate service and forward the requests accordingly. By leveraging Kubernetes' services and health checks, high-availability of the OpenStack endpoints is achieved transparently: a simple round-robin DNS that resolves to few Kubernetes' nodes is sufficient.

When it comes to data availability for Cinder and Glance, Stackanetes relies on the storage backend being used.

High availability is not yet guaranteed for Elasticsearch (Searchlight).

[services]: http://kubernetes.io/docs/user-guide/services/

## Getting started

### Preparing the environment

#### Kubernetes

To setup Kubernetes, the [CoreOS guides] may be used.

At least two nodes must be labelled for Stackanetes' usage:

    kubectl label node minion1 openstack-control-plane=enabled
    kubectl label node minion2 openstack-compute-node=enabled

Following Galera guidelines, it's required to keep odd number of `openstack-control-plane` nodes. For development setup purposes, it's allowed to build one-node cluster.

[CoreOS guides]: https://coreos.com/kubernetes/docs/latest/

#### DNS

To enable Nova's live-migration, there must be a DNS server, accessible inside the cluster, able to resolve each hostname of the Kubernetes nodes. The IP address of this server will then have to be provided in the Stackanetes [configuration].

If external access is wanted, the Ingress feature should be enabled in Stackanetes [configuration] and the external DNS environment should be configured to resolve the following names (modulo a custom host that may have been configured) to at least some Kubernetes' nodes:

    identity.openstack.cluster
    horizon.openstack.cluster
    image.openstack.cluster
    network.openstack.cluster
    volume.openstack.cluster
    compute.openstack.cluster
    novnc.compute.openstack.cluster
    search.openstack.cluster

[configuration]: #configuration

#### Ceph

If data high availability, Nova's live migration or Cinder is desired, Ceph must be used. Deploying Ceph can be achieved easily [using bare containers] or even by [using kubernetes].

Few users and pools have to be created. The user and pool names can be customized. Note down the keyrings, they will be used in the [configuration].

    ceph osd pool create volumes 128
    ceph osd pool create images 128
    ceph osd pool create vms 128
    ceph auth get-or-create client.cinder mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=volumes, allow rwx pool=vms, allow rx pool=images'
    ceph auth get-or-create client.glance mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=images'

[using bare containers]: https://github.com/ceph/ceph-docker
[using kubernetes]: https://github.com/ceph/ceph-docker/tree/master/examples/kubernetes
[configuration]: #configuration

#### kpm

[kpm](https://github/coreos/kpm) is the package manager and command-line tool used to deploy stackanetes. It can either be installed from PyPI or directly from source:

    # PyPI
    sudo pip install kpm --pre

    # Source
    git clone https://github.com/coreos/kpm.git
    cd kpm && sudo make install

Moving forward, we'll need to use a kpm registry. The hosted registry `https://beta.kpm.sh` can be used if there is no desire of pushing a modified version of Stackanetes. Otherwise, a private one may be deployed - using kpm itself:

    kpm deploy coreos/kpm-registry --namespace kpm -H https://beta.kpm.sh

It will then be available on `http://kpm-registry.kpm`.

### Deploying

#### Cloning

Technically, cloning Stackanetes is not necessary beside getting the default configuration file but is believed to be a good practice to understand the architecture of the project or if modifying the project is intended.

    git clone https://github.com/stackanetes/stackanetes.git
    cd stackanetes

#### Configuration

All the configuration is done in one place: the `parameters.yaml` file in the `stackanetes` meta-package. The file is self-documented.

While it is no strictly necessary, it is possible to persist changes to that file for reproducible deployments across environments, without the need of sharing the it out of band. To do this, the stackanetes meta-package has to be pushed, which is currently only possible on a private registry - and because a private registry is used, every packages have to be pushed. Pushing may also be needed when modifications are made to Stackanetes. Here is the simplest way to push the meta-package:

    cd stackanetes
    kpm push -H http://kpm-registry.kpm -f
    cd ..

#### Deployment

All we have to do is ask kpm to deploy Stackanetes. In the example below, we specify a namespace, a configuration file containing all non-default parameters (`stackanetes/parameters.yaml` if the changes have been made in place) and the registry where the packages should be pulled.

    kpm deploy stackanetes/stackanetes --namespace openstack --variables stackanetes/parameters.yaml -H https://beta.kpm.sh

For a finer-grained deployment story, kpm also supports versioning and release channels.

### Access

Once Stackanetes is fully deployed, we can log in to Horizon or use the CLI directly.

If Ingress is enabled, Horizon may be accessed on http://horizon.openstack.cluster:30080/. Otherwise, it will be available on port 80 of any defined external IP. The default credentials are _admin_ / _password_.

The file [env_openstack.sh](env_openstack.sh) contains the default environment variables that will enable interaction using the various OpenStack clients.

### Update

When the configuration is updated (e.g. a new Ceph monitor is added) or customized packages are pushed, Stackanetes can be updated with the exact same command that has been used to deploy it. kpm will compute the differences between the actual deployment and the desired one and update the required resources: it will for instance trigger a rolling upgrade when a deployment is modified.

Note that manual rollouts still have to be done when only [ConfigMaps] are modified.

[ConfigMaps]: http://kubernetes.io/docs/user-guide/configmap/
