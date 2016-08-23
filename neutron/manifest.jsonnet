local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "quentinm/neutron",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "neutron",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      node_label: "openstack-control-plane",
      replicas: 1,

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",

        init: $.variables.deployment.image.base % "kolla-toolbox",
        db_sync: $.variables.deployment.image.base % "neutron-server",
        server: $.variables.deployment.image.base % "neutron-server",
        dhcp: $.variables.deployment.image.base % "neutron-dhcp-agent",
        l3: $.variables.deployment.image.base % "neutron-l3-agent",
        neutron_openvswitch_agent: $.variables.deployment.image.base % "neutron-openvswitch-agent",
        openvswitch_db_server: $.variables.deployment.image.base % "openvswitch-db-server",
        openvswitch_vswitchd: $.variables.deployment.image.base % "openvswitch-vswitchd",
        post: $.variables.deployment.image.base % "kolla-toolbox",
      },
    },

    network: {
      ip_address: "{{ .IP }}",
      minion_interface_name: "eno1",

      dns:  {
        ip: "10.3.0.10",
        domain: "cluster.local",
      },

      port: {
        server: 9696,
      },

      ingress: {
        enabled: true,
        host: "%s.openstack.cluster",
        port: 30080,

        named_host: $.variables.network.ingress.host % "network",
      },
    },

    database: {
      address: "mariadb",
      port: 3306,
      root_user: "root",
      root_password: "password",

      neutron_user: "neutron",
      neutron_password: "password",
      neutron_database_name: "neutron",
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

      neutron_user: "neutron",
      neutron_password: "password",
      neutron_region_name: "RegionOne",

      nova_user: "nova",
      nova_password: "password",
      nova_region_name: "RegionOne",
    },

    nova: {
      auth_url: "http://nova-api:8774",
    },

    neutron: {
      bridge_name: "br-ex",
    },

    misc: {
      debug: false,
      workers: 8,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/dhcp-agent.ini.yaml",
      template: (importstr "templates/configmaps/dhcp-agent.ini.yaml"),
      name: "neutron-dhcpagentini",
      type: "configmap",
    },

    {
      file: "configmaps/dnsmasq.conf.yaml",
      template: (importstr "templates/configmaps/dnsmasq.conf.yaml"),
      name: "neutron-dnsmasqconf",
      type: "configmap",
    },

    {
      file: "configmaps/init.sh.yaml",
      template: (importstr "templates/configmaps/init.sh.yaml"),
      name: "neutron-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/l3-agent.ini.yaml",
      template: (importstr "templates/configmaps/l3-agent.ini.yaml"),
      name: "neutron-l3agentini",
      type: "configmap",
    },

    {
      file: "configmaps/ml2-conf.ini.yaml",
      template: (importstr "templates/configmaps/ml2-conf.ini.yaml"),
      name: "neutron-ml2confini",
      type: "configmap",
    },

    {
      file: "configmaps/neutron-openvswitch-agent.sh.yaml",
      template: (importstr "templates/configmaps/neutron-openvswitch-agent.sh.yaml"),
      name: "neutron-neutronopenvswitchagentsh",
      type: "configmap",
    },

    {
      file: "configmaps/neutron.conf.yaml",
      template: (importstr "templates/configmaps/neutron.conf.yaml"),
      name: "neutron-neutronconf",
      type: "configmap",
    },

    {
      file: "configmaps/openvswitch-db-server.sh.yaml",
      template: (importstr "templates/configmaps/openvswitch-db-server.sh.yaml"),
      name: "neutron-openvswitchdbserversh",
      type: "configmap",
    },

    {
      file: "configmaps/openvswitch-ensure-configured.sh.yaml",
      template: (importstr "templates/configmaps/openvswitch-ensure-configured.sh.yaml"),
      name: "neutron-openvswitchensureconfiguredsh",
      type: "configmap",
    },

    {
      file: "configmaps/openvswitch-vswitchd.sh.yaml",
      template: (importstr "templates/configmaps/openvswitch-vswitchd.sh.yaml"),
      name: "neutron-openvswitchvswitchdsh",
      type: "configmap",
    },

    {
      file: "configmaps/post.sh.yaml",
      template: (importstr "templates/configmaps/post.sh.yaml"),
      name: "neutron-postsh",
      type: "configmap",
    },

    {
      file: "configmaps/resolv.conf.yaml",
      template: (importstr "templates/configmaps/resolv.conf.yaml"),
      name: "neutron-resolvconf",
      type: "configmap",
    },

    // Init.
    {
      file: "init.yaml",
      template: (importstr "templates/init.yaml"),
      name: "neutron-init",
      type: "job",
    },

    {
      file: "db-sync.yaml",
      template: (importstr "templates/db-sync.yaml"),
      name: "neutron-db-sync",
      type: "job",
    },

    {
      file: "post.yaml",
      template: (importstr "templates/post.yaml"),
      name: "neutron-post",
      type: "job",
    },

    // Daemons.
    {
      file: "server/deployment.yaml",
      template: (importstr "templates/server/deployment.yaml"),
      name: "neutron-server",
      type: "deployment",
    },

    {
      file: "agents.yaml",
      template: (importstr "templates/agents.yaml"),
      name: "neutron-agents",
      type: "deployment",
    },

    {
      file: "openvswitch.yaml",
      template: (importstr "templates/openvswitch.yaml"),
      name: "neutron-openvswitch",
      type: "deployment",
    },

    // Services.
    {
      file: "server/service.yaml",
      template: (importstr "templates/server/service.yaml"),
      name: "neutron-server",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "server/ingress.yaml",
        template: (importstr "templates/server/ingress.yaml"),
        name: "neutron-server",
        type: "ingress",
      },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
