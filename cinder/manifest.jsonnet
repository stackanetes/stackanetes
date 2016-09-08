local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/cinder",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "cinder",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      control_node_label: "openstack-control-plane",
      replicas: 1,

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",

        init: $.variables.deployment.image.base % "kolla-toolbox",
        db_sync: $.variables.deployment.image.base % "cinder-api",
        api: $.variables.deployment.image.base % "cinder-api",
        volume: $.variables.deployment.image.base % "cinder-volume",
        scheduler: $.variables.deployment.image.base % "cinder-scheduler",
      },
    },

    network: {
      ip_address: "{{ .IP }}",
      port: 8776,

      ingress: {
        enabled: true,
        host: "%s.openstack.cluster",
        port: 30080,

        named_host: $.variables.network.ingress.host % "volume",
      },
    },

    database: {
      address: "mariadb",
      port: 3306,
      root_user: "root",
      root_password: "password",

      cinder_user: "cinder",
      cinder_password: "password",
      cinder_database_name: "cinder",
    },

    keystone: {
      auth_uri: "http://keystone-api:5000",
      auth_url: "http://keystone-api:35357",
      admin_user: "admin",
      admin_password: "password",
      admin_project_name: "admin",
      admin_region_name: "RegionOne",
      auth: "{'auth_url':'%s', 'username':'%s','password':'%s','project_name':'%s','domain_name':'default'}" % [$.variables.keystone.auth_url, $.variables.keystone.admin_user, $.variables.keystone.admin_password, $.variables.keystone.admin_project_name],

      cinder_user: "cinder",
      cinder_password: "password",
      cinder_region_name: "RegionOne",
    },

    rabbitmq: {
      address: "rabbitmq",
      admin_user: "rabbitmq",
      admin_password: "password",
    },

    ceph: {
      monitors: [],

      cinder_user: "cinder",
      cinder_pool: "volumes",
      cinder_keyring: "",
      secret_uuid: "",
    },

    glance: {
      api_url: "http://glance-api:9292",
    },

    misc: {
      debug: false,
      workers: 8,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/ceph.client.cinder.keyring.yaml.j2",
      template: (importstr "templates/configmaps/ceph.client.cinder.keyring.yaml.j2"),
      name: "cinder-cephclientcinderkeyring",
      type: "configmap",
    },

    {
      file: "configmaps/ceph.conf.yaml.j2",
      template: (importstr "templates/configmaps/ceph.conf.yaml.j2"),
      name: "cinder-cephconf",
      type: "configmap",
    },

    {
      file: "configmaps/cinder.conf.yaml.j2",
      template: (importstr "templates/configmaps/cinder.conf.yaml.j2"),
      name: "cinder-cinderconf",
      type: "configmap",
    },

    {
      file: "configmaps/init.sh.yaml.j2",
      template: (importstr "templates/configmaps/init.sh.yaml.j2"),
      name: "cinder-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/db-sync.sh.yaml.j2",
      template: (importstr "templates/configmaps/db-sync.sh.yaml.j2"),
      name: "cinder-dbsyncsh",
      type: "configmap",
    },

    // Init.
    {
      file: "init.yaml.j2",
      template: (importstr "templates/init.yaml.j2"),
      name: "cinder-init",
      type: "job",
    },

    {
      file: "db-sync.yaml.j2",
      template: (importstr "templates/db-sync.yaml.j2"),
      name: "cinder-db-sync",
      type: "job",
    },

    // Deployments.
    {
      file: "api.yaml.j2",
      template: (importstr "templates/api.yaml.j2"),
      name: "cinder-api",
      type: "deployment",
    },

    {
      file: "scheduler.yaml.j2",
      template: (importstr "templates/scheduler.yaml.j2"),
      name: "cinder-scheduler",
      type: "deployment",
    },

    {
      file: "volume.yaml.j2",
      template: (importstr "templates/volume.yaml.j2"),
      name: "cinder-volume",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: "cinder-api",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "ingress.yaml.j2",
        template: (importstr "templates/ingress.yaml.j2"),
        name: "cinder-api",
        type: "ingress",
      },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
