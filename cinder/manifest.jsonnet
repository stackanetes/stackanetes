local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "quentinm/cinder",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "cinder",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      node_label: "openstack-control-plane",
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

    rados_gateway: {
      enabled: true,
      ceph_admin_keyring: "",
      ceph_monitors: [],
      secret_uuid: "",

      cinder_user: "cinder",
      cinder_pool: "volumes",
      cinder_backup_pool: "backups",
      nova_pool: "vms",
      glance_pool: "images",
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
      file: "configmaps/ceph.client.admin.keyring.yaml",
      template: (importstr "templates/configmaps/ceph.client.admin.keyring.yaml"),
      name: "cinder-cephclientadminkeyring",
      type: "configmap",
    },

    {
      file: "configmaps/ceph.conf.yaml",
      template: (importstr "templates/configmaps/ceph.conf.yaml"),
      name: "cinder-cephconf",
      type: "configmap",
    },

    {
      file: "configmaps/cinder.conf.yaml",
      template: (importstr "templates/configmaps/cinder.conf.yaml"),
      name: "cinder-cinderconf",
      type: "configmap",
    },

    {
      file: "configmaps/init.sh.yaml",
      template: (importstr "templates/configmaps/init.sh.yaml"),
      name: "cinder-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/db-sync.sh.yaml",
      template: (importstr "templates/configmaps/db-sync.sh.yaml"),
      name: "cinder-dbsyncsh",
      type: "configmap",
    },

    {
      file: "configmaps/cinder-volume.sh.yaml",
      template: (importstr "templates/configmaps/cinder-volume.sh.yaml"),
      name: "cinder-cindervolumesh",
      type: "configmap",
    },

    // Init.
    {
      file: "init.yaml",
      template: (importstr "templates/init.yaml"),
      name: "cinder-init",
      type: "job",
    },

    {
      file: "db-sync.yaml",
      template: (importstr "templates/db-sync.yaml"),
      name: "cinder-db-sync",
      type: "job",
    },

    // Daemons.
    {
      file: "api.yaml",
      template: (importstr "templates/api.yaml"),
      name: "cinder-api",
      type: "deployment",
    },

    {
      file: "scheduler.yaml",
      template: (importstr "templates/scheduler.yaml"),
      name: "cinder-scheduler",
      type: "deployment",
    },

    {
      file: "volume.yaml",
      template: (importstr "templates/volume.yaml"),
      name: "cinder-volume",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml",
      template: (importstr "templates/service.yaml"),
      name: "cinder-api",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "ingress.yaml",
        template: (importstr "templates/ingress.yaml"),
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
