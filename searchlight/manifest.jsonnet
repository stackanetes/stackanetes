local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/searchlight",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "searchlight",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      control_node_label: "openstack-control-plane",
      replicas: 1,

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",

        init: $.variables.deployment.image.base % "kolla-toolbox",
        api: $.variables.deployment.image.base % "searchlight",
      },
    },

    network: {
      port: {
        api: 9393,
      },

      ingress: {
        enabled: true,
        host: "%s.openstack.cluster",
        port: 30080,

        named_host: $.variables.network.ingress.host % "search",
      },
    },

    rabbitmq: {
      address: "rabbitmq",
      admin_user: "rabbitmq",
      admin_password: "password",
    },

    keystone: {
      auth_uri: "http://keystone-api:5000",
      auth_url: "http://keystone-api:35357",
      admin_user: "admin",
      admin_password: "password",
      admin_project_name: "admin",
      admin_region_name: "RegionOne",
      auth: "{'auth_url':'%s', 'username':'%s','password':'%s','project_name':'%s','domain_name':'default'}" % [$.variables.keystone.auth_url, $.variables.keystone.admin_user, $.variables.keystone.admin_password, $.variables.keystone.admin_project_name],

      searchlight_user: "nova",
      searchlight_password: "password",
      searchlight_region_name: "RegionOne",
    },

    elasticsearch: {
      address: "searchlight-es",
    },

    misc: {
      debug: false,
      workers: 8,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/api-paste.ini.yaml.j2",
      template: (importstr "templates/configmaps/api-paste.ini.yaml.j2"),
      name: "searchlight-apipasteini",
      type: "configmap",
    },

    {
      file: "configmaps/init.sh.yaml.j2",
      template: (importstr "templates/configmaps/init.sh.yaml.j2"),
      name: "searchlight-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/policy.json.yaml.j2",
      template: (importstr "templates/configmaps/policy.json.yaml.j2"),
      name: "searchlight-policyjson",
      type: "configmap",
    },

    {
      file: "configmaps/searchlight.conf.yaml.j2",
      template: (importstr "templates/configmaps/searchlight.conf.yaml.j2"),
      name: "searchlight-searchlightconf",
      type: "configmap",
    },

    // Init.
    {
      file: "init.yaml.j2",
      template: (importstr "templates/init.yaml.j2"),
      name: "searchlight-init",
      type: "job",
    },

    // Deployments.
    {
      file: "deployment.yaml.j2",
      template: (importstr "templates/deployment.yaml.j2"),
      name: "searchlight-api",
      type: "deployment",
    },

    // Services.
    {
      file: "service.yaml.j2",
      template: (importstr "templates/service.yaml.j2"),
      name: "searchlight-api",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "ingress.yaml.j2",
        template: (importstr "templates/ingress.yaml.j2"),
        name: "searchlight-api",
        type: "ingress",
      },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
