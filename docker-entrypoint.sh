#!/bin/bash
set -eo pipefail
echo Testing kubectl
if [[ ! $(kubectl get nodes) ]] ; then 
	echo Cannot connect to Kubernetes, please make sure you have the correct kubeconfig
	exit 1;
fi
if [[ ! $(kubectl get nodes -o json | grep controller ) ]] ; then
	echo Cannot find a node with app=persistent-control label 
	exit 1;
fi

if [[ ! $(kubectl get nodes -o json | grep compute ) ]] ; then 
	echo Cannot find a node with app=compute label 
	exit 1;
fi

echo Modifying stackanetes.conf
builderip=$(cat /etc/stackanetes/stackanetes.conf | grep 2181 | awk '{print $3}')

sed -i "s@#host = $builderip@host = $ZK_HOST@g" /etc/stackanetes/stackanetes.conf
sed -i 's@#kubectl_path@kubectl_path@g' /etc/stackanetes/stackanetes.conf
sed -i "s@#tag = 1.0.0@tag = $IMAGE_VERSION@g" /etc/stackanetes/stackanetes.conf
sed -i "s@#minion_interface_name = eno1@minion_interface_name = $HOST_INTERFACE@g" /etc/stackanetes/stackanetes.conf


echo Deploying stackanetes
stackanetes --config-dir /etc/stackanetes run all --debug
