local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "quentinm/mariadb",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "mariadb",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      node_label: "openstack-control-plane",
      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",
        mariadb: $.variables.deployment.image.base % "mariadb",
      },
    },

    network: {
      ip_address: "{{ .IP }}",

      port: {
        mariadb: 3306,
        wsrep: 4567,
        ist: 4568,
        sst: 4444,
      },
    },

    database: {
      // Initial root's password.
      root_password: "password",

      // Cluster configuration.
      // TODO: Replace node_name. .HOSTNAME can't get replaced properly
      // by the kubernetes-entrypoint on rkt because the ev variable doesn't
      // exist. POD_NAME however does exist but it would be better to just get
      // it from the container instead.
      node_name: "master",
      cluster_name: "mariadb",
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/my.cnf.yaml",
      template: (importstr "templates/configmaps/my.cnf.yaml"),
      name: "mariadb-mycnf",
      type: "configmap",
    },

    {
      file: "configmaps/start.sh.yaml",
      template: (importstr "templates/configmaps/start.sh.yaml"),
      name: "mariadb-startsh",
      type: "configmap",
    },

    // Daemons.
    {
      file: "deployment.yaml",
      template: (importstr "templates/deployment.yaml"),
      name: "mariadb",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml",
      template: (importstr "templates/service.yaml"),
      name: "mariadb",
      type: "service",
    },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
