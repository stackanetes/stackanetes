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

    ingress_enabled: true,
    ingress_host: "%s.openstack.cluster",
    ingress_port: 30080,
  },

  local dependencies = [
    // Data plane.
    { name: "quentinm/mariadb" },
    { name: "quentinm/rabbitmq" },
    { name: "quentinm/memcached" },

    // OpenStack services.
    { name: "quentinm/keystone" },
    { name: "quentinm/glance" },
    { name: "quentinm/horizon" },
  ]
  // Ceph-specific dependencies
  + (if $.variables.ceph_enabled == true then
  [
    { name: "quentinm/rados-gateway" }
  ] else [ ])
  // Ingress-specific dependencies
  + (if $.variables.ingress_enabled == true then
  [
    { name: "quentinm/traefik" }
  ] else [ ]),

  deploy: [defaults.set_vars(dependency, $.variables) for dependency in dependencies]
}, params)
