local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/rabbitmq",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.2.0",
    description: "rabbitmq",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      control_node_label: "openstack-control-plane",

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:newton",
        rabbitmq: $.variables.deployment.image.base % "rabbitmq",
      },

      volumes: {
        rabbitmq_data: "emptyDir: {}"
      },

    },

    network: {
      ip_address: "{{ .IP }}",
      ip_address_erlang: "{{ .IP_ERLANG }}",

      port: {
        rabbitmq: 5672,
        epmd: 4369,
        cluster: 25672,
        management: 15672,
      },
    },

    rabbitmq: {
      admin_user: "rabbitmq",
      admin_password: "password",
      erlang_cookie: "ERLANG_COOKIE",
      node_startup_timeout: 180,
      probe_timeout: 10,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/enabled_plugins.yaml.j2",
      template: (importstr "templates/configmaps/enabled_plugins.yaml.j2"),
      name: "rabbitmq-enabledplugins",
      type: "configmap",
    },

    {
      file: "configmaps/rabbitmq-env.conf.yaml.j2",
      template: (importstr "templates/configmaps/rabbitmq-env.conf.yaml.j2"),
      name: "rabbitmq-rabbitmqenvconf",
      type: "configmap",
    },

    {
      file: "configmaps/rabbitmq.config.yaml.j2",
      template: (importstr "templates/configmaps/rabbitmq.config.yaml.j2"),
      name: "rabbitmq-rabbitmqconfig",
      type: "configmap",
    },

    {
      file: "configmaps/rabbitmq-definitions.json.yaml.j2",
      template: (importstr "templates/configmaps/rabbitmq-definitions.json.yaml.j2"),
      name: "rabbitmq-rabbitmqdefinitions",
      type: "configmap",
    },

    {
      file: "configmaps/rabbitmq-scripts.sh.yaml.j2",
      template: (importstr "templates/configmaps/rabbitmq-scripts.sh.yaml.j2"),
      name: "rabbitmq-scripts",
      type: "configmap",
    },

    {
      file: "configmaps/rabbitmq-erlang.cookie.yaml.j2",
      template: (importstr "templates/configmaps/rabbitmq-erlang.cookie.yaml.j2"),
      name: "rabbitmq-erlangcookie",
      type: "configmap",
    },


    // Deamonset. This needs to be moved to deployment on K8S 1.4 with anit-affinity.
    {
      file: "daemonset.yaml.j2",
      template: (importstr "templates/daemonset.yaml.j2"),
      name: "rabbitmq",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: "rabbitmq",
      type: "service",
    }
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
