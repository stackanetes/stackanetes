FROM ubuntu:14.04

env DOCKER_REGISTRY quay.io/stackanetes
env HOST_INTERFACE eno2
env IMAGE_VERSION 2.0.0

WORKDIR /stackanetes

RUN apt-get update && \
	apt-get -y install python-pip python-dev libffi-dev libssl-dev git curl 

RUN curl -O https://storage.googleapis.com/kubernetes-release/release/v1.3.0-alpha.4/bin/linux/amd64/kubectl && \
	mv kubectl /usr/bin/kubectl && \
	chmod +x /usr/bin/kubectl 

RUN pip install --upgrade pip 

COPY . /stackanetes

RUN pip install -r requirements.txt && \
	python setup.py build && python setup.py install && \
	./generate_config_file_sample.sh && \	
	rm /stackanetes/Dockerfile

ENTRYPOINT ["/stackanetes/docker-entrypoint.sh"]
