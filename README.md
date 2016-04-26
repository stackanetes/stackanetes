Required: python2.7, git, pip, kubectl
Download that repo.
Using pip install all requirements from requirements.txt

bash generate_config_file_samples.sh

cp kolla-k8s/etc/globals.yml /etc/kolla-k8s/
cp kolla-k8s/etc/kolla-k8s.conf.sample /etc/kolla-k8s/kolla-k8s.conf
cp kolla-k8s/etc/passwords.yml /etc/kolla-k8s/

set following variables in kolla-k8s.conf
[k8s]
host
kubectl_path
yml_dir_path
[zookeeper]
host

python setup.pt build
python setup.py install

mkdir /usr/local/share/kolla-k8s/etc
cp /openstack-on-k8s/all.yml /usr/local/share/kolla-k8s/etc/

kolla_k8s --config-dir /etc/kolla-k8s/ run <service-name>
