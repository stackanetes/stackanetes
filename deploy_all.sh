#!/bin/bash

services="keystone-api keystone-init keystone-db-sync glance-init glance-db-sync glance-api glance-registry glance-api glance-post nova-init nova-api nova-conductor nova-consoleauth nova-novncproxy nova-scheduler nova-post nova-api-db-sync memcached horizon neutron-init neutron-server-db-sync neutron-server neutron-post neutron-openvswitch-agent openvswitch-node network-node compute-node nova-api-db-sync"
for service in $services

do
  kolla-k8s --config-dir /etc/kolla-k8s kill $service
done
for service in $services

do
  kolla-k8s --config-dir /etc/kolla-k8s run $service
done

