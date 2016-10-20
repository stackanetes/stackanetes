local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/keystone",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.2.0",
    description: "keystone",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      control_node_label: "openstack-control-plane",
      replicas: 1,

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",

        init: $.variables.deployment.image.base % "kolla-toolbox",
        db_sync: $.variables.deployment.image.base % "keystone-api",
        api: $.variables.deployment.image.base % "keystone-api",
      },
    },

    network: {
      ip_address: "{{ .IP }}",

      port: {
        public: 5000,
        admin: 35357,
      },

      ingress: {
        enabled: true,
        host: "%s.openstack.cluster",
        port: 30080,

        named_host: $.variables.network.ingress.host % "identity",
      },
    },

    database: {
      address: "mariadb",
      port: 3306,
      root_user: "root",
      root_password: "password",

      keystone_user: "keystone",
      keystone_password: "password",
      keystone_database_name: "keystone",
    },

    keystone: {
      // Initial admin's region, project and user.
      admin_user: "admin",
      admin_password: "password",
      admin_project_name: "admin",
      admin_region_name: "RegionOne",
    },

    memcached: {
      address: "memcached:11211",
    },

    misc: {
      workers: 8,
      debug: true,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/init.sh.yaml.j2",
      template: (importstr "templates/configmaps/init.sh.yaml.j2"),
      name: "keystone-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/db-sync.sh.yaml.j2",
      template: (importstr "templates/configmaps/db-sync.sh.yaml.j2"),
      name: "keystone-dbsyncsh",
      type: "configmap",
    },

    {
      file: "configmaps/start.sh.yaml.j2",
      template: (importstr "templates/configmaps/start.sh.yaml.j2"),
      name: "keystone-startsh",
      type: "configmap",
    },

    {
      file: "configmaps/keystone.conf.yaml.j2",
      template: (importstr "templates/configmaps/keystone.conf.yaml.j2"),
      name: "keystone-keystoneconf",
      type: "configmap",
    },

    {
      file: "configmaps/wsgi-keystone.conf.yaml.j2",
      template: (importstr "templates/configmaps/wsgi-keystone.conf.yaml.j2"),
      name: "keystone-wsgikeystone",
      type: "configmap",
    },

    {
      file: "configmaps/mpm_event.conf.yaml.j2",
      template: (importstr "templates/configmaps/mpm_event.conf.yaml.j2"),
      name: "keystone-mpmeventconf",
      type: "configmap",
    },

    // Init.
    {
      file: "init.yaml.j2",
      template: (importstr "templates/init.yaml.j2"),
      name: "keystone-init",
      type: "job",
    },

    {
      file: "db-sync.yaml.j2",
      template: (importstr "templates/db-sync.yaml.j2"),
      name: "keystone-db-sync",
      type: "job",
    },

    // Deployments.
    {
      file: "deployment.yaml.j2",
      template: (importstr "templates/deployment.yaml.j2"),
      name: "keystone-api",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: "keystone-api",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "api/ingress.yaml.j2",
        template: (importstr "templates/ingress.yaml.j2"),
        name: "keystone-api",
        type: "ingress",
      },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
