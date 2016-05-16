FROM ubuntu:14.04

env KOLLA_K8S_YMLPATH /stackanetes/rc
env ZK_HOST zookeeper:2181
env NEUTRON_CNI eth0
env DEST_YML_FILES_DIR /stackanetes/rc
env DOCKER_REGISTRY quay.io/stackanetes
env HOST_INTERFACE eno2
env IMAGE_VERSION 2.0.0
env KUBECONFIG ''
env KUBEHOST ''

WORKDIR /stackanetes

RUN apt-get update && \
	apt-get -y install python-pip python-dev libffi-dev libssl-dev git curl 

RUN pip install --upgrade pip && \
    pip install ansible && \     
    curl -O https://storage.googleapis.com/kubernetes-release/release/v1.2.3/bin/linux/amd64/kubectl && \
	mv kubectl /usr/bin/kubectl && \
	chmod +x /usr/bin/kubectl 

COPY . /stackanetes

RUN pip install -r requirements.txt && \
	python setup.py build && python setup.py install && \
	./generate_config_file_sample.sh && \	
	rm /stackanetes/Dockerfile

ENTRYPOINT ["/stackanetes/docker-entrypoint.sh"]
