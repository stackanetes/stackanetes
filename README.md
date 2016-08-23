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

In addition to these, a few other applications are deployed:
- MariaDB
- Memcached
- RabbitMQ
- RADOS Gateway
- Traefik

Services are divided and scheduled into two groups, except from few services that run everywhere (e.g. Open vSwitch agents, Traefik):
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

### High-availability & Networking

Thanks to Kubernetes' [deployments](http://kubernetes.io/docs/user-guide/deployments/), common OpenStack APIs can be made highly-available using a single parameter, called `replicas`.

Internal traffic (i.e. inside the Kubernetes cluster) is load-balanced natively using Kubernetes' [services](http://kubernetes.io/docs/user-guide/services/). When Ingress is enabled, external access (i.e. from outside of the Kubernetes cluster), can be done and guaranteed using a simple Round-Robin DNS pointing to every nodes exposing Traefik (i.e. every nodes labeled to deploy Stackanetes). Traefik will then forward requests through the Kubernetes load-balancing mechanism, which has awareness of each service health.

If Ceph is enabled, data availability for Cinder and Glance is assured by the storage backend itself.

## Getting started

### Customize

    TODO

### Deploy

First of all, at least two nodes must be labelled for Stackanetes' usage:

    kubectl label node minion1 openstack-control-plane=enabled
    kubectl label node minion2 openstack-compute-node=enabled

If Ingress is enabled (default), the DNS environment should be configured to resolve the following names (modulo a custom Ingress host that may have been configured) to the nodes that have been labeled:

    identity.openstack.cluster
    horizon.openstack.cluster
    image.openstack.cluster
    network.openstack.cluster
    volume.openstack.cluster
    compute.openstack.cluster
    novnc.compute.openstack.cluster

Then,

    TODO

### Access

Once Stackanetes is entirely deployed, we can log in to Horizon or use the CLI directly.

If Ingress is enabled, Horizon may be accessed on http://horizon.openstack.cluster:30080/. Otherwise, it will be available on port 80 of any defined external IP. The default credentials are _admin_ / _password_.

The file [env_openstack.sh](env_openstack.sh) contains the default environment variables required to interact with OpenStack using the `openstack` client.

### Update

    TODO

## Limitations

Some features haven't been implemented yet in Stackanetes:
- MariaDB, Memcached, RabbitMQ are not deployed in a highly-available manner,
- Some OpenStack features are missing (see components list above),
- Compute services can't be ran using the rkt container runtime,
- SSL/TLS is not terminated.
