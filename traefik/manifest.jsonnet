local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/traefik",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "traefik",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      control_replicas: 1,

      image: {
        traefik: "traefik:latest",
      },
    },

    network: {
      port: {
        http: 30080,
        https: 30443,
        ui: 8080,
      },
    },
  },

  resources: [
    // Deployments.
    {
      file: "deployment.yaml.j2",
      template: (importstr "templates/deployment.yaml.j2"),
      name: "traefik",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: "traefik",
      type: "service",
    },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
