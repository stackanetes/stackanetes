FROM ubuntu:14.04

env KUBEHOST localhost:8001
env KOLLA_K8S_YMLPATH /stackenetes/rc
env ZK_HOST zookeeper:30000 
env NEUTRON_CNI eth0
env NEUTRON_HOSTIF eno2
env KUBECONFIG /stackenetes/kubeconfig
env KUBECONFIG_CONTEXT stackpoint
env DEST_YML_FILES_DIR /stackenetes/rc
env DOCKER_REGISTRY quay.io/stackanetes
env HOST_INTERFACE eno1
env IMAGE_VERSION 2.0.0

WORKDIR /stackenetes

RUN apt-get update && \
	apt-get -y install python-pip python-dev libffi-dev libssl-dev git curl 

RUN pip install --upgrade pip && \
    pip install ansible && \     
    curl -O https://storage.googleapis.com/kubernetes-release/release/v1.2.3/bin/linux/amd64/kubectl && \
	mv kubectl /usr/bin/kubectl && \
	chmod +x /usr/bin/kubectl 

COPY . /stackenetes     

RUN pip install -r requirements.txt && \
	python setup.py build && python setup.py install && \
	./generate_config_file_sample.sh && \	
	rm /stackenetes/Dockerfile

ENTRYPOINT ["/stackenetes/docker-entrypoint.sh"]
