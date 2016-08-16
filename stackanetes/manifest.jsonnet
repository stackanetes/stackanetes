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
    namespace: "default",

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
  },

  deploy: [defaults.set_vars(dependency, $.variables) for dependency in
    [
      // Data plane.
      { name: "quentinm/mariadb" },
      { name: "quentinm/rabbitmq" },
      { name: "quentinm/memcached" },
      //if $.variables.ceph_enabled then
        { name: "quentinm/rados-gateway" },

      // OpenStack APIs.
      { name: "quentinm/keystone" },
      { name: "quentinm/glance" },
    ]
  ]
}, params)
