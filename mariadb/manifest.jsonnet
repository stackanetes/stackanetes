local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/mariadb",
    expander: "jinja2",
    author: "Mateusz Blaszkowski",
    version: "0.1.0",
    description: "mariadb",
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
      dns:  {
        servers: ["10.3.0.10"],
        kubernetes_domain: "cluster.local",
        other_domains: "",
      },

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
      template: (importstr "templates/configmaps/seed.sh.yaml.j2"),
      name: "mariadb-seedsh",
      type: "configmap",
    },

    {
      file: "configmaps/bootstrap-db.sh.yaml.j2",
      template: (importstr "templates/configmaps/bootstrap-db.sh.yaml.j2"),
      name: "bootstrap-db",
      type: "configmap",
    },

    {
      file: "configmaps/start.sh.yaml.j2",
      template: (importstr "templates/configmaps/start.sh.yaml.j2"),
      name: "mariadb-startsh",
      type: "configmap",
    },

    {
      file: "configmaps/peer-finder.py.yaml.j2",
      template: (importstr "templates/configmaps/peer-finder.py.yaml.j2"),
      name: "mariadb-peer-finder",
      type: "configmap",
    },

    {
      file: "configmaps/charsets.cnf.yaml.j2",
      template: (importstr "templates/configmaps/charsets.cnf.yaml.j2"),
      name: "mariadb-charsets",
      type: "configmap",
    },

    {
      file: "configmaps/engine.cnf.yaml.j2",
      template: (importstr "templates/configmaps/engine.cnf.yaml.j2"),
      name: "mariadb-engine",
      type: "configmap",
    },

    {
      file: "configmaps/galera-my.yaml.j2",
      template: (importstr "templates/configmaps/galera-my.cnf.yaml.j2"),
      name: "mariadb-mycnf",
      type: "configmap",
    },

    {
      file: "configmaps/log.cnf.yaml.j2",
      template: (importstr "templates/configmaps/log.cnf.yaml.j2"),
      name: "mariadb-log",
      type: "configmap",
    },

    {
      file: "configmaps/networking.cnf.yaml.j2",
      template: (importstr "templates/configmaps/networking.cnf.yaml.j2"),
      name: "mariadb-networking",
      type: "configmap",
    },

    {
      file: "configmaps/pid.cnf.yaml.j2",
      template: (importstr "templates/configmaps/pid.cnf.yaml.j2"),
      name: "mariadb-pid",
      type: "configmap",
    },

    {
      file: "configmaps/tuning.cnf.yaml.j2",
      template: (importstr "templates/configmaps/tuning.cnf.yaml.j2"),
      name: "mariadb-tuning",
      type: "configmap",
    },

    {
      file: "configmaps/replicas.py.yaml.j2",
      template: (importstr "templates/configmaps/replicas.py.yaml.j2"),
      name: "mariadb-replicas",
      type: "configmap",
    },

    {
      file: "configmaps/wsrep.cnf.yaml.j2",
      template: (importstr "templates/configmaps/wsrep.cnf.yaml.j2"),
      name: "mariadb-wsrep",
      type: "configmap",
    },

    // Jobs.
    {
      file: "init.yaml.j2",
      template: (importstr "templates/init.yaml.j2"),
      name: "mariadb-init",
      type: "job",
    },

    // DaemonSets.
    {
      file: "daemonset.yaml.j2",
      template: (importstr "templates/daemonset.yaml.j2"),
      name: "mariadb",
      type: "daemonset",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: "mariadb",
      type: "service",
    }
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
