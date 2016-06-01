#!/bin/bash
sudo python setup.py install
kolla-k8s --config-dir /etc/kolla-k8s --debug kill $1
kolla-k8s --config-dir /etc/kolla-k8s --debug run $1
