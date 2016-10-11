#!/bin/bash
set +x

# Load environment.
. env_openstack.sh

# Install command-line tools.
pip install python-neutronclient python-openstackclient -U

# Import CoreOS / CirrOS images.
cd /tmp

wget http://download.cirros-cloud.net/0.3.3/cirros-0.3.3-x86_64-disk.img
wget https://stable.release.core-os.net/amd64-usr/current/coreos_production_openstack_image.img.bz2
bunzip2 coreos_production_openstack_image.img.bz2

openstack image create CoreOS --container-format bare --disk-format qcow2 --file /tmp/coreos_production_openstack_image.img --public
openstack image create CirrOS --container-format bare --disk-format qcow2 --file /tmp/cirros-0.3.3-x86_64-disk.img --public

rm coreos_production_openstack_image.img
rm cirros-0.3.3-x86_64-disk.img

# Create external network.
openstack network create ext-net --external --provider-physical-network physnet1 --provider-network-type flat
openstack subnet create ext-subnet --no-dhcp --allocation-pool start=172.16.0.2,end=172.16.0.249 --network=ext-net --subnet-range 172.16.0.0/24 --gateway 172.16.0.1

# Create default flavors.
openstack flavor create --public m1.tiny --ram 512 --disk 1 --vcpus 1
openstack flavor create --public m1.small --ram 2048 --disk 20 --vcpus 1
openstack flavor create --public m1.medium --ram 4096 --disk 40 --vcpus 2
openstack flavor create --public m1.large --ram 8192 --disk 80 --vcpus 4
openstack flavor create --public m1.xlarge --ram 16384 --disk 160 --vcpus 8

# Create a demo tenant network, router and security group.
openstack network create demo-net
openstack subnet create demo-subnet --allocation-pool start=192.168.0.2,end=192.168.0.254 --network demo-net --subnet-range 192.168.0.0/24 --gateway 192.168.0.1 --dns-nameserver 8.8.8.8 --dns-nameserver 8.8.4.4
openstack router create demo-router
neutron router-interface-add demo-router $(openstack subnet show demo-subnet -c id -f value)
neutron router-gateway-set demo-router ext-net

#openstack security group rule create default --protocol icmp
#openstack security group rule create default --protocol tcp --dst-port 22

# Create keypair.
openstack keypair create demo-key > ./stackanetes.id_rsa

# Create a CoreOS instance.
openstack server create demo-coreos \
  --image $(openstack image show CoreOS -c id -f value) \
  --flavor $(openstack flavor show m1.small -c id -f value) \
  --nic net-id=$(openstack network show demo-net -c id -f value) \
  --key-name demo-key

# Allocate and attach a floating IP to the instance.
openstack ip floating add $(openstack ip floating create ext-net -c floating_ip_address -f value) demo-coreos

# Create a volume and attach it to the instance.
openstack volume create demo-volume --size 10
sleep 10
openstack server add volume demo-coreos demo-volume

# Live migrate the instance.
# openstack server migrate --live b1-3 demo-coreos

# Boot instance from volume.
openstack volume create demo-boot-volume --image $(openstack image show CoreOS -c id -f value) --size 10

openstack server create demo-coreos-boot-volume \
  --volume $(openstack volume show demo-boot-volume -c id -f value) \
  --flavor $(openstack flavor show m1.small -c id -f value) \
  --nic net-id=$(openstack network show demo-net -c id -f value) \
  --key-name demo-key
