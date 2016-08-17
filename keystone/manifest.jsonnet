local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "quentinm/keystone",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "keystone",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      node_label: "openstack-control-plane",
      replicas: 1,

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",

        init: $.variables.deployment.image.base % "kolla-toolbox",
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
        // External dependency configuration.
        enabled: true,
        host: "%s.openstack.cluster",
        port: 30080,

        // Glance configuration.
        named_host: $.variables.network.ingress.host % "identity",
      },
    },

    database: {
      // External dependency configuration.
      address: "mariadb",
      port: 3306,
      root_user: "root",
      root_password: "password",

      // Keystone configuration.
      keystone_user: "keystone",
      keystone_password: "password",
      keystone_database_name: "keystone",
    },

    // Initial admin's region, project and user.
    admin_user: "admin",
    admin_password: "password",
    admin_project_name: "admin",
    admin_region_name: "RegionOne",

    misc: {
      workers: 8,
      debug: true,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/init.sh.yaml",
      template: (importstr "templates/configmaps/init.sh.yaml"),
      name: "keystone-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/db-sync.sh.yaml",
      template: (importstr "templates/configmaps/db-sync.sh.yaml"),
      name: "keystone-dbsyncsh",
      type: "configmap",
    },

    {
      file: "configmaps/start.sh.yaml",
      template: (importstr "templates/configmaps/start.sh.yaml"),
      name: "keystone-startsh",
      type: "configmap",
    },

    {
      file: "configmaps/keystone.conf.yaml",
      template: (importstr "templates/configmaps/keystone.conf.yaml"),
      name: "keystone-keystoneconf",
      type: "configmap",
    },

    {
      file: "configmaps/wsgi-keystone.conf.yaml",
      template: (importstr "templates/configmaps/wsgi-keystone.conf.yaml"),
      name: "keystone-wsgikeystone",
      type: "configmap",
    },

    // Init.
    {
      file: "init.yaml",
      template: (importstr "templates/init.yaml"),
      name: "keystone-init",
      type: "job",
    },

    {
      file: "db-sync.yaml",
      template: (importstr "templates/db-sync.yaml"),
      name: "keystone-db-sync",
      type: "job",
    },

    // Daemons.
    {
      file: "deployment.yaml",
      template: (importstr "templates/deployment.yaml"),
      name: "keystone-api",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml",
      template: (importstr "templates/service.yaml"),
      name: "keystone-api",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "api/ingress.yaml",
        template: (importstr "templates/ingress.yaml"),
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
