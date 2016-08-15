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
    namespace: "default",

    deployment: {
      node_label: "openstack-control-plane",
      replicas: 1,

      image: {
          api: "quay.io/stackanetes/stackanetes-keystone-api:barcelona",
          init: "quay.io/stackanetes/stackanetes-kolla-toolbox:barcelona",
          db_sync: "quay.io/stackanetes/stackanetes-keystone-api:barcelona",
      },
    },

    network: {
      ip_address: "{% raw %}{{ .IP }}{% endraw %}",
      port: {
        public: 5000,
        admin: 35357,
      },
      ingress: {
        enabled: true,
        host: "identity.openstack.cluster",
      },
    },

    database: {
      // Dependency configuration.
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
    if $.variables.network.ingress.enabled then
      {
        file: "ingress.yaml",
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
