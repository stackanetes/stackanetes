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
      replicas: 1,

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
      file: "deployment.yaml",
      template: (importstr "templates/deployment.yaml"),
      name: "traefik",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml",
      template: (importstr "templates/service.yaml"),
      name: "traefik",
      type: "service",
    },

    {
      file: "service-ui.yaml",
      template: (importstr "templates/service-ui.yaml"),
      name: "traefik-ui",
      type: "service",
    },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
