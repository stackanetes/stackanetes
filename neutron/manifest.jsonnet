local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/neutron",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.2.0",
    description: "neutron",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      control_node_label: "openstack-control-plane",
      control_replicas: 1,

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",

        init: $.variables.deployment.image.base % "kolla-toolbox",
        db_sync: $.variables.deployment.image.base % "neutron-server",
        server: $.variables.deployment.image.base % "neutron-server",
        dhcp: $.variables.deployment.image.base % "neutron-dhcp-agent",
        metadata: $.variables.deployment.image.base % "neutron-metadata-agent",
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

      nova: {
        address: "nova-api"  ,
      },

      dns:  {
        servers: ["10.3.0.10"],
        kubernetes_domain: "cluster.local",
        other_domains: "",
      },

      port: {
        server: 9696,
        metadata: 8775,
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

    memcached: {
      address: "memcached:11211",
    },

    rabbitmq: {
      address: "rabbitmq",
      admin_user: "rabbitmq",
      admin_password: "password",
      port: 5672
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
      metadata_secret: "password"
    },

    misc: {
      debug: false,
      workers: 8,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/dhcp-agent.ini.yaml.j2",
      template: (importstr "templates/configmaps/dhcp-agent.ini.yaml.j2"),
      name: "neutron-dhcpagentini",
      type: "configmap",
    },

    {
      file: "configmaps/metadata-agent.ini.yaml.j2",
      template: (importstr "templates/configmaps/metadata-agent.ini.yaml.j2"),
      name: "neutron-metadataagentini",
      type: "configmap",
    },

    {
      file: "configmaps/dnsmasq.conf.yaml.j2",
      template: (importstr "templates/configmaps/dnsmasq.conf.yaml.j2"),
      name: "neutron-dnsmasqconf",
      type: "configmap",
    },

    {
      file: "configmaps/init.sh.yaml.j2",
      template: (importstr "templates/configmaps/init.sh.yaml.j2"),
      name: "neutron-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/l3-agent.ini.yaml.j2",
      template: (importstr "templates/configmaps/l3-agent.ini.yaml.j2"),
      name: "neutron-l3agentini",
      type: "configmap",
    },

    {
      file: "configmaps/ml2-conf.ini.yaml.j2",
      template: (importstr "templates/configmaps/ml2-conf.ini.yaml.j2"),
      name: "neutron-ml2confini",
      type: "configmap",
    },

    {
      file: "configmaps/neutron-openvswitch-agent.sh.yaml.j2",
      template: (importstr "templates/configmaps/neutron-openvswitch-agent.sh.yaml.j2"),
      name: "neutron-neutronopenvswitchagentsh",
      type: "configmap",
    },

    {
      file: "configmaps/neutron.conf.yaml.j2",
      template: (importstr "templates/configmaps/neutron.conf.yaml.j2"),
      name: "neutron-neutronconf",
      type: "configmap",
    },

    {
      file: "configmaps/openvswitch-db-server.sh.yaml.j2",
      template: (importstr "templates/configmaps/openvswitch-db-server.sh.yaml.j2"),
      name: "neutron-openvswitchdbserversh",
      type: "configmap",
    },

    {
      file: "configmaps/openvswitch-ensure-configured.sh.yaml.j2",
      template: (importstr "templates/configmaps/openvswitch-ensure-configured.sh.yaml.j2"),
      name: "neutron-openvswitchensureconfiguredsh",
      type: "configmap",
    },

    {
      file: "configmaps/openvswitch-vswitchd.sh.yaml.j2",
      template: (importstr "templates/configmaps/openvswitch-vswitchd.sh.yaml.j2"),
      name: "neutron-openvswitchvswitchdsh",
      type: "configmap",
    },

    {
      file: "configmaps/post.sh.yaml.j2",
      template: (importstr "templates/configmaps/post.sh.yaml.j2"),
      name: "neutron-postsh",
      type: "configmap",
    },

    {
      file: "configmaps/resolv.conf.yaml.j2",
      template: (importstr "templates/configmaps/resolv.conf.yaml.j2"),
      name: "neutron-resolvconf",
      type: "configmap",
    },

    // Init.
    {
      file: "init.yaml.j2",
      template: (importstr "templates/init.yaml.j2"),
      name: "neutron-init",
      type: "job",
    },

    {
      file: "db-sync.yaml.j2",
      template: (importstr "templates/db-sync.yaml.j2"),
      name: "neutron-db-sync",
      type: "job",
    },

    {
      file: "post.yaml.j2",
      template: (importstr "templates/post.yaml.j2"),
      name: "neutron-post",
      type: "job",
    },

    // Deployments.
    {
      file: "server/deployment.yaml.j2",
      template: (importstr "templates/server/deployment.yaml.j2"),
      name: "neutron-server",
      type: "deployment",
    },

    // Daemonsets.
    {
      file: "openvswitch.yaml.j2",
      template: (importstr "templates/openvswitch.yaml.j2"),
      name: "neutron-openvswitch",
      type: "deployment",
    },

    {
      file: "agents/dhcp-agent.yaml.j2",
      template: (importstr "templates/agents/dhcp-agent.yaml.j2"),
      name: "neutron-dhcp-agent",
      type: "deployment",
    },

    {
      file: "agents/l3-agent.yaml.j2",
      template: (importstr "templates/agents/l3-agent.yaml.j2"),
      name: "neutron-l3-agent",
      type: "deployment",
    },

    {
      file: "agents/metadata-agent.yaml.j2",
      template: (importstr "templates/agents/metadata-agent.yaml.j2"),
      name: "neutron-metadata-agent",
      type: "deployment",
    },

    // Services.
    {
      file: "server/service.yaml.j2",
      template: (importstr "templates/server/service.yaml.j2"),
      name: "neutron-server",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "server/ingress.yaml.j2",
        template: (importstr "templates/server/ingress.yaml.j2"),
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
