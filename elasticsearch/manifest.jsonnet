local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/elasticsearch",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "elasticsearch",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      engine: "docker",
      control_node_label: "openstack-control-plane",
      app_label: "elasticsearch",
      image: {
        elasticsearch: "elasticsearch:2.3.5",
      },
    },

    network: {
      port: {
        api: 9200,
        cluster: 9300,
      },
    },
  },

  resources: [
    // Deployments.
    {
      file: "deployment.yaml.j2",
      template: (importstr "templates/deployment.yaml.j2"),
      name: $.variables.deployment.app_label,
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: $.variables.deployment.app_label,
      type: "service",
    },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
