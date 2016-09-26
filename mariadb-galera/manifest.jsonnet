local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/mariadb-galera",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "mariadb-galera",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      control_node_label: "openstack-control-plane",
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
      file: "configmaps/seed.sh.yaml.j2",
      template: (importstr "templates/configmaps/mariadb-galera-seed.sh.yaml.j2"),
      name: "mariadb-galera-seedsh",
      type: "configmap",
    },

    {
      file: "configmaps/mariadb-galera-start.sh.yaml.j2",
      template: (importstr "templates/configmaps/mariadb-galera-start.sh.yaml.j2"),
      name: "mariadb-galera-startsh",
      type: "configmap",
    },

    {
      file: "configmaps/peer-finder.py.yaml.j2",
      template: (importstr "templates/configmaps/peer-finder.py.yaml.j2"),
      name: "mariadb-galera-peer-finder",
      type: "configmap",
    },

    {
      file: "configmaps/charsets.cnf.yaml.j2",
      template: (importstr "templates/configmaps/charsets.cnf.yaml.j2"),
      name: "mariadb-galera-charsets",
      type: "configmap",
    },

    {
      file: "configmaps/engine.cnf.yaml.j2",
      template: (importstr "templates/configmaps/engine.cnf.yaml.j2"),
      name: "mariadb-galera-engine",
      type: "configmap",
    },

    {
      file: "configmaps/galera-my.yaml.j2",
      template: (importstr "templates/configmaps/galera-my.cnf.yaml.j2"),
      name: "mariadb-galera-mycnf",
      type: "configmap",
    },

    {
      file: "configmaps/log.cnf.yaml.j2",
      template: (importstr "templates/configmaps/log.cnf.yaml.j2"),
      name: "mariadb-galera-log",
      type: "configmap",
    },

    {
      file: "configmaps/networking.cnf.yaml.j2",
      template: (importstr "templates/configmaps/networking.cnf.yaml.j2"),
      name: "mariadb-galera-networking",
      type: "configmap",
    },

    {
      file: "configmaps/pid.cnf.yaml.j2",
      template: (importstr "templates/configmaps/pid.cnf.yaml.j2"),
      name: "mariadb-galera-pid",
      type: "configmap",
    },

    {
      file: "configmaps/tuning.cnf.yaml.j2",
      template: (importstr "templates/configmaps/tuning.cnf.yaml.j2"),
      name: "mariadb-galera-tuning",
      type: "configmap",
    },

    {
      file: "configmaps/wsrep.cnf.yaml.j2",
      template: (importstr "templates/configmaps/wsrep.cnf.yaml.j2"),
      name: "mariadb-galera-wsrep",
      type: "configmap",
    },

    // Jobs.
    {
      file: "init.yaml.j2",
      template: (importstr "templates/init.yaml.j2"),
      name: "mariadb-galera-init",
      type: "job",
    },

    // DaemonSets.
    {
      file: "daemonset.yaml.j2",
      template: (importstr "templates/daemonset.yaml.j2"),
      name: "mariadb-galera-ds",
      type: "daemonset",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: "mariadb-galera",
      type: "service",
    }
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
