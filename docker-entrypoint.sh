#!/bin/bash
set -eo pipefail
echo Testing kubectl
if [[ ! $(kubectl get nodes) ]] ; then 
  echo Cannot connect to Kubernetes, please make sure you have the correct kubeconfig
  exit 1;
fi
if [[ ! $(kubectl get nodes -o json | grep controller ) ]] ; then
  echo Cannot find a node with app=control label
  exit 1;
fi

if [[ ! $(kubectl get nodes -o json | grep compute ) ]] ; then 
  echo Cannot find a node with app=compute label
  exit 1;
fi

echo Modifying stackanetes.conf

sed -i 's@#kubectl_path@kubectl_path@g' /etc/stackanetes/stackanetes.conf
sed -i "s@#docker_image_tag = mitaka@docker_image_tag = $IMAGE_VERSION@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#minion_interface_name = eno1@minion_interface_name = $HOST_INTERFACE@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#docker_registry = quay.io/stackanetes@docker_registry = $DOCKER_REGISTRY@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#dns_ip = 10.2.0.10@dns_ip = $DNS_IP@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#cluster_name = cluster.local@cluster_name = $CLUSTER_NAME@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#external_ip = 10.10.10.10@external_ip = $EXTERNAL_IP@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#namespace = stackanetes@namespace = $NAMESPACE@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#image_prefix =@image_prefix = $IMAGE_PREFIX@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#ceph_mons = 192.168.10.1,10.91.10.2@ceph_mons = $CEPH_MONS@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#ceph_admin_keyring = ASDA==@ceph_admin_keyring = $CEPH_ADMIN_KEYRING@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#ceph_enabled = true@ceph_enabled = $CEPH_ENABLED@g" /etc/stackanetes/stackanetes.conf

echo Deploying stackanetes
python ./manage_all.py kill
python ./manage_all.py run
