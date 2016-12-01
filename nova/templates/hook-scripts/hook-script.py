#!/bin/python
import kubernetes.config
import socket
import sys
import time
import yaml

from kubernetes import watch, client as k8sclient
from keystoneauth1 import identity, session
from novaclient import client, exceptions

OPENRC_PATH = "/openrc.yaml"
ACCEPTABLE_OPERATIONS = ["poststart_compute", "prestop_compute", "prestop_libvirt"]


def load_configs(openrc_parh=OPENRC_PATH):
    with open(openrc_parh, 'r') as stream:
            try:
                config = yaml.load(stream)
            except yaml.YAMLError as e:
                print "Cannot load configs: {}".format(e)
                sys.exit(1)

    return config


def get_sessions():
    config = load_configs()
    try:
        auth = identity.v3.Password(
            auth_url=config["OS_AUTH_URL"],
            username=config["OS_USERNAME"],
            password=config["OS_PASSWORD"],
            project_name=config["OS_PROJECT_NAME"],
            user_domain_id=config["OS_USER_DOMAIN_ID"],
            project_domain_id=config["OS_PROJECT_DOMAIN_ID"]
        )
        keystone_session = session.Session(auth=auth)
    except Exception as e:
        print "Cannot create session: {}".format(e)
        sys.exit(1)

    return keystone_session


def get_nova_client():
    keystone_session = get_sessions()
    try:
        nova_client = client.Client(
            version="2.1",
            session=keystone_session,
            endpoint_type="internalURL"
        )
    except Exception as e:
        print "Cannot create nova_client: {}".format(e)
        sys.exit(1)

    return nova_client


def disable_node(nclient, hostname):
    try:
        nclient.services.disable_log_reason(
            hostname, "nova-compute", "Kubernetes-drain")
    except exceptions.NotFound as e:
        print "Cannot find node to disable {}: {}".format(hostname, e)
        sys.exit(1)


def enable_node(nclient, hostname):
    try:
        nclient.services.enable(hostname, "nova-compute")
    except exceptions.NotFound as e:
        print "Cannot find node to enable {}: {}".format(hostname, e)
        sys.exit(1)


def check_node_status(hostname):
    v1 = k8sclient.CoreV1Api()
    nodes = v1.list_node(watch=False)
    for node in nodes.items:
        if hostname == node.metadata.name:
            return node.spec.unschedulable

    print "Cannot find node {}".format(hostname)
    sys.exit(1)


def get_all_vms_deployed_on_host(nclient, hostname):
    try:
        vms = nclient.servers.findall(**{"OS-EXT-SRV-ATTR:host": hostname})
        return vms
    except Exception as e:
        print "Cannot retrieve vm list: {}".format(e)
        sys.exit(1)


def live_migrate_host(nclient, hostname):
    vms = get_all_vms_deployed_on_host(nclient, hostname)
    all_vms = len(vms)
    not_migrated_vms = []
    for vm in vms:
        try:
            if vm._info["os-extended-volumes:volumes_attached"]:
                vm.live_migrate(block_migration=False)
            else:
                vm.live_migrate(block_migration=True)
        except Exception as e:
            not_migrated_vms.append(vm)
            print "Cannot live migrate vm {}: {}".format(vm.id, e)
    vms = [vm for vm in vms if vm not in not_migrated_vms]
    migrate_vms = len(vms)
    print "{} of {} are being migrated.".format(migrate_vms, all_vms)
    live_migration_status(vms, hostname)


def live_migration_status(vms, hostname):
    while vms:
        migrated_vms = []
        for vm in vms:
            vm.get()
            if vm._info["OS-EXT-SRV-ATTR:host"] != hostname:
                migrated_vms.append(vm.id)
                print "VM {} has been migrated. {} left.".format(
                    vm.id, len(vms) - len(migrated_vms))
        vms = [vm for vm in vms if vm.id not in migrated_vms]
        if vms:
            time.sleep(5)


def check_compute_status(hostname):
    v1 = k8sclient.CoreV1Api()

    w = watch.Watch()
    for event in w.stream(v1.list_pod_for_all_namespaces):
        if event['type'] == "DELETED" and \
                        event['object'].metadata.generate_name == "nova-compute-" and \
                        event['object'].spec.node_name == hostname:
            print "Nova-compute has been deleted, " \
                  "nova-libvirt is going down."


def poststart_compute(hostname):
    nova_client = get_nova_client()
    enable_node(nova_client, hostname)


def prestop_compute(hostname):
    # check whether node is unschedulable
    if check_node_status(hostname):
        print "Node is drained."
        nova_client = get_nova_client()
        disable_node(nova_client, hostname)
        live_migrate_host(nova_client, hostname)
    else:
        print "Node is in a schedulable state. Nova-compute is shutting down."


def prestop_libvirt(hostname):
    check_compute_status(hostname)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Invalid number of arguments."
        sys.exit(1)
    if sys.argv[1] not in ACCEPTABLE_OPERATIONS:
        print "Invalid argument. Acceptable arguments: {}.".format(", ".join(ACCEPTABLE_OPERATIONS))
        sys.exit(1)

    kubernetes.config.load_incluster_config()
    hostname = socket.gethostname()
    locals()[sys.argv[1]](hostname)

