local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/rabbitmq",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "rabbitmq",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      control_node_label: "openstack-control-plane",

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",
        rabbitmq: $.variables.deployment.image.base % "rabbitmq",
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

    # Credentials.
    rabbitmq: {
      admin_user: "rabbitmq",
      admin_password: "password",
      erlang_cookie: "ERLANG_COOKIE",
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/rabbitmq-clusterer.config.yaml.j2",
      template: (importstr "templates/configmaps/rabbitmq-clusterer.config.yaml.j2"),
      name: "rabbitmq-rabbitmqclustererconfig",
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
      file: "configmaps/start.sh.yaml.j2",
      template: (importstr "templates/configmaps/start.sh.yaml.j2"),
      name: "rabbitmq-startsh",
      type: "configmap",
    },

    // Deployments.
    {
      file: "deployment.yaml.j2",
      template: (importstr "templates/deployment.yaml.j2"),
      name: "rabbitmq",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: "rabbitmq",
      type: "service",
    },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
