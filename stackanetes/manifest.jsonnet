local kpm = import "kpm.libjsonnet";

function(
  params={}
)

local defaults = import 'defaults.libjsonnet';

kpm.package({
  package: {
    name: "quentinm/stackanetes",
    expander: "jinja2",
    author: "Antoine Legrand",
    version: "0.1.1",
    description: "stackanetes",
    license: "Apache 2.0",
  },

  variables: {
    image_base: "quay.io/stackanetes/stackanetes-%s:barcelona",

    external_ips: [
      "192.168.0.201",
    ],

    ceph_enabled: true,
    ceph_monitors: [
      "192.168.0.207",
      "192.168.0.209",
      "192.168.0.211",
    ],
    ceph_admin_keyring: "AQCW84RXpk6mERAA9hfAIKzV1uwYC5C1ogN4QA==",
    ceph_rbd_secret_uuid: "bbc5b4d5-6fca-407d-807d-06a4f4a7bccb",

    ingress_enabled: true,
    ingress_host: "%s.openstack.cluster",
    ingress_port: 30080,
  },

  local dependencies = [
    // Utility services.
    if $.variables.ingress_enabled == true then
      { name: "quentinm/traefik" },

    // Data plane.
    { name: "quentinm/mariadb" },
    { name: "quentinm/rabbitmq" },
    { name: "quentinm/memcached" },
    if $.variables.ceph_enabled == true then
      { name: "quentinm/rados-gateway" },

    // OpenStack services.
    { name: "quentinm/keystone" },
    { name: "quentinm/glance" },
    if $.variables.ceph_enabled == true then
      { name: "quentinm/cinder" },
    { name: "quentinm/horizon" },
  ],

  deploy: [defaults.set_vars(dependency, $.variables) for dependency in dependencies]
}, params)
