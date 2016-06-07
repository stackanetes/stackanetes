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

echo Modifying kolla-k8s.conf
builderip=$(cat /etc/kolla-k8s/kolla-k8s.conf | grep 2181 | awk '{print $3}')

sed -i "s@#host = $builderip@host = $ZK_HOST@g" /etc/kolla-k8s/kolla-k8s.conf
sed -i 's@#kubectl_path@kubectl_path@g' /etc/kolla-k8s/kolla-k8s.conf
sed -i "s@#tag = 1.0.0@tag = $IMAGE_VERSION@g" /etc/kolla-k8s/kolla-k8s.conf
sed -i "s@#host_interface = eno1@host_interface = $HOST_INTERFACE@g" /etc/kolla-k8s/kolla-k8s.conf

echo Modifying Globals.yml
sed -i "s@network_interface: \"eth0\"@network_interface: \"$NEUTRON_CNI\"@g" /etc/kolla-k8s/globals.yml
sed -i "s@neutron_external_interface: \"eth0\"@neutron_external_interface: \"$HOST_INTERFACE\"@g" /etc/kolla-k8s/globals.yml
sed -i "s@enable_horizon: \"no\"@enable_horizon: \"yes\"@g" /etc/kolla-k8s/globals.yml

#Wait for zookeeper to come online on k8s cluster
while [ true  ]                                                                                                                                                                                
do                                                                                                                                                                                             
    sleep 2                                                                                                                                                                                    
    ZOOKEEPER_ENDPOINTS=$(kubectl describe svc zookeeper |awk '/Endpoint/ {{print $2}}' |head -1)                                                                                      
    ZOOKEEPER_ENDPOINTS_ARRAY=(${ZOOKEEPER_ENDPOINTS//,/ })                                                                                                                                  
    if [ ${#ZOOKEEPER_ENDPOINTS_ARRAY[@]} -eq 3 ]; then                                                                                                                                              
        break                                                                                                                                                                                  
    fi                                                                                                                                                                                         
done 

echo Deploying stackanetes
kolla-k8s --config-dir /etc/kolla-k8s run all --debug
