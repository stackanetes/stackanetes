#!/bin/bash
set -eo pipefail
echo Testing kubectl
if [[ ! $(kubectl get nodes) ]] ; then 
	echo Cannot connect to Kubernetes, please make sure you have the correct kubeconfig
	exit ;	
fi
if [[ ! $(kubectl get nodes -o json | grep persistent-control ) ]] ; then 
	echo Cannot find a node with app=persistent-control label 
	exit ;	
fi
if [[ ! $(kubectl get nodes -o json | grep non-persistent-control ) ]] ; then 
	echo Cannot find a node with app=non-persistent-control label 
	exit ;	
fi
if [[ ! $(kubectl get nodes -o json | grep compute ) ]] ; then 
	echo Cannot find a node with app=compute label 
	exit ;	
fi

echo Modifying kolla-k8s.con
builderip=$(cat /etc/kolla-k8s/kolla-k8s.conf | grep 2181 | awk '{print $3}')
sed -i "s@#host = $builderip@host = $ZK_HOST@g" /etc/kolla-k8s/kolla-k8s.conf
sed -i 's@#kubectl_path@kubectl_path@g' /etc/kolla-k8s/kolla-k8s.conf
sed -i "s@#yml_dir_path = rc/@yml_dir_path = $KOLLA_K8s_YMLPATH@g" /etc/kolla-k8s/kolla-k8s.conf
sed -i "s@#kubeconfig_path =@kubeconfig_path = $KUBECONFIG@g" /etc/kolla-k8s/kolla-k8s.conf
sed -i "s@#deployment_id = root@deployment_id = root@g" /etc/kolla-k8s/kolla-k8s.conf
sed -i "s@#host =@host = $KUBEHOST@g" /etc/kolla-k8s/kolla-k8s.conf

echo Modifying Globals.yml
sed -i "s@network_interface: \"eth0\"@network_interface: \"$NEUTRON_CNI\"@g" /etc/kolla-k8s/globals.yml
sed -i "s@neutron_external_interface: \"eth0\"@neutron_external_interface: \"$NEUTRON_HOSTIF\"@g" /etc/kolla-k8s/globals.yml
sed -i "s@enable_horizon: \"no\"@enable_horizon: \"yes\"@g" /etc/kolla-k8s/globals.yml

echo modifying all.yml
sed -i "s@dest_yml_files_dir: /var/lib/kolla-k8s@dest_yml_files_dir: $dest_yml_files_dir@g"  /stackenetes/ansible/group_vars/all.yml
sed -i "s@docker_registry: quay.io/stackanetes@docker_registry: $docker_registry@g"  /stackenetes/ansible/group_vars/all.yml
sed -i "s@host_interface: eno1@host_interface: $host_interface @g"  /stackenetes/ansible/group_vars/all.yml
sed -i "s@image_version: 2.0.0@image_version: $image_version@g"  /stackenetes/ansible/group_vars/all.yml

echo Executing ansible playbook
cd ansible
ansible-playbook site.yml
# there seems to be an extra horizon yml file that shouldn't get executed with "kolla-k8s run all"

echo Deploying Zookeeper
kolla-k8s --config-dir /etc/kolla-k8s run zookeeper

while [ true  ]                                                                                                                                                                                
do                                                                                                                                                                                             
    sleep 2                                                                                                                                                                                    
    zookeeper_service_endpoints=$(kubectl describe svc zookeeper |awk '/Endpoint/ {{print $2}}' |head -1)                                                                                      
    zookeeper_endpoints=(${zookeeper_service_endpoints//,/ })                                                                                                                                  
    if [ ${#zookeeper_endpoints[@]} -eq 3 ]; then                                                                                                                                              
        break                                                                                                                                                                                  
    fi                                                                                                                                                                                         
done 

echo Deploying stackenetes
kolla-k8s --config-dir /etc/kolla-k8s run all --debug
