local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/rados-gateway",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "rados-gateway",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      node_label: "openstack-control-plane",
      replicas: 1,
      image: {
        ceph_daemon: "ceph/daemon:latest"
      },
    },

    network: {
      external_ips: [],
      port: 6000,
    },

    ceph: {
      monitors: [],

      rgw_user: "rgw",
      rgw_keyring: "",
    },

    rados_gateway: {
      user_uid: "glance",
      user_display_name: "User for Glance",
      user_temp_url_key: "glance_temp_url_key",
      subuser: "glance:swift",
      subuser_secret: "",
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/ceph.client.rgw.keyring.yaml",
      template: (importstr "templates/configmaps/ceph.client.rgw.keyring.yaml"),
      name: "rados-gateway-cephclientrgwkeyring",
      type: "configmap",
    },

    {
      file: "configmaps/ceph.conf.yaml",
      template: (importstr "templates/configmaps/ceph.conf.yaml"),
      name: "rados-gateway-cephconf",
      type: "configmap",
    },

    {
      file: "configmaps/start.sh.yaml",
      template: (importstr "templates/configmaps/start.sh.yaml"),
      name: "rados-gateway-startsh",
      type: "configmap",
    },

    // Daemons.
    {
      file: "deployment.yaml",
      template: (importstr "templates/deployment.yaml"),
      name: "rados-gateway",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml",
      template: (importstr "templates/service.yaml"),
      name: "rados-gateway",
      type: "service",
    },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
