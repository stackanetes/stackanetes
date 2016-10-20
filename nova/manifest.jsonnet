local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/nova",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "nova",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      engine: "docker",
      control_node_label: "openstack-control-plane",
      compute_node_label: "openstack-compute-node",

      replicas: 1,

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",

        init: $.variables.deployment.image.base % "kolla-toolbox",
        db_sync: $.variables.deployment.image.base % "nova-api",
        drain: $.variables.deployment.image.base % "nova-drain",
        api: $.variables.deployment.image.base % "nova-api",
        conductor: $.variables.deployment.image.base % "nova-conductor",
        scheduler: $.variables.deployment.image.base % "nova-scheduler",
        novncproxy: $.variables.deployment.image.base % "nova-novncproxy",
        consoleauth: $.variables.deployment.image.base % "nova-consoleauth",
        compute: $.variables.deployment.image.base % "nova-compute",
        libvirt: $.variables.deployment.image.base % "nova-libvirt",
        post: $.variables.deployment.image.base % "kolla-toolbox",
      },
    },

    network: {
      ip_address: "{{ .IP }}",
      external_ips: [],
      minion_interface_name: "eno1",
      dns:  {
        servers: ["10.3.0.10"],
        kubernetes_domain: "cluster.local",
        other_domains: "",
      },

      port: {
        api: 8774,
        metadata: 8775,
        novncproxy: 6080,
      },

      ingress: {
        enabled: true,
        host: "%s.openstack.cluster",
        port: 30080,

        named_host: {
          api: $.variables.network.ingress.host % "compute",
          novncproxy: $.variables.network.ingress.host % "novnc.compute",
        }
      },
    },

    nova: {
      drain_timeout: 15,
    },

    database: {
      address: "mariadb",
      port: 3306,
      root_user: "root",
      root_password: "password",

      nova_user: "nova",
      nova_password: "password",
      nova_database_name: "nova",
      nova_api_database_name: "nova_api"
    },

    keystone: {
      auth_uri: "http://keystone-api:5000",
      auth_url: "http://keystone-api:35357",
      admin_user: "admin",
      admin_password: "password",
      admin_project_name: "admin",
      admin_region_name: "RegionOne",
      domain_name: "default",
      tenant_name: "admin",
      auth: "{'auth_url':'%s', 'username':'%s','password':'%s','project_name':'%s','domain_name':'%s'}" % [$.variables.keystone.auth_url, $.variables.keystone.admin_user, $.variables.keystone.admin_password, $.variables.keystone.admin_project_name, $.variables.keystone.domain_name],

      neutron_user: "neutron",
      neutron_password: "password",
      neutron_region_name: "RegionOne",

      nova_user: "nova",
      nova_password: "password",
      nova_region_name: "RegionOne",
    },

    rabbitmq: {
      address: "rabbitmq",
      admin_user: "rabbitmq",
      admin_password: "password",
      port: 5672
    },

    ceph: {
      enabled: true,
      monitors: [],

      cinder_user: "cinder",
      cinder_keyring: "",
      nova_pool: "vms",
      secret_uuid: "",
    },

    glance: {
      api_url: "http://glance-api:9292",
    },

    neutron: {
      api_url: "http://neutron-server:9696",
      metadata_secret: "password",
    },

    memcached: {
      address: "memcached:11211",
    },
    
    misc: {
      debug: false,
      workers: 8,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/init.sh.yaml.j2",
      template: (importstr "templates/configmaps/init.sh.yaml.j2"),
      name: "nova-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/openrc.yaml.j2",
      template: (importstr "templates/configmaps/openrc.yaml.j2"),
      name: "nova-openrc",
      type: "configmap",
    },

    {
      file: "configmaps/drain-conf.yaml.j2",
      template: (importstr "templates/configmaps/drain-conf.yaml.j2"),
      name: "nova-drainconf",
      type: "configmap",
    },

    {
      file: "configmaps/db-sync.sh.yaml.j2",
      template: (importstr "templates/configmaps/db-sync.sh.yaml.j2"),
      name: "nova-dbsyncsh",
      type: "configmap",
    },

    {
      file: "configmaps/post.sh.yaml.j2",
      template: (importstr "templates/configmaps/post.sh.yaml.j2"),
      name: "nova-postsh",
      type: "configmap",
    },

    {
      file: "configmaps/nova.conf.yaml.j2",
      template: (importstr "templates/configmaps/nova.conf.yaml.j2"),
      name: "nova-novaconf",
      type: "configmap",
    },

    {
      file: "configmaps/nova.sh.yaml.j2",
      template: (importstr "templates/configmaps/nova.sh.yaml.j2"),
      name: "nova-novash",
      type: "configmap",
    },

    {
      file: "configmaps/resolv.conf.yaml.j2",
      template: (importstr "templates/configmaps/resolv.conf.yaml.j2"),
      name: "nova-resolvconf",
      type: "configmap",
    },

    {
      file: "configmaps/libvirtd.conf.yaml.j2",
      template: (importstr "templates/configmaps/libvirtd.conf.yaml.j2"),
      name: "nova-libvirtdconf",
      type: "configmap",
    },

    {
      file: "configmaps/ceph.client.cinder.keyring.yaml.j2",
      template: (importstr "templates/configmaps/ceph.client.cinder.keyring.yaml.j2"),
      name: "nova-cephclientcinderkeyring",
      type: "configmap",
    },

    {
      file: "configmaps/ceph.conf.yaml.j2",
      template: (importstr "templates/configmaps/ceph.conf.yaml.j2"),
      name: "nova-cephconf",
      type: "configmap",
    },

    {
      file: "configmaps/libvirt.sh.yaml.j2",
      template: (importstr "templates/configmaps/libvirt.sh.yaml.j2"),
      name: "nova-libvirtsh",
      type: "configmap",
    },

    {
      file: "configmaps/virsh-set-secret.sh.yaml.j2",
      template: (importstr "templates/configmaps/virsh-set-secret.sh.yaml.j2"),
      name: "nova-virshsetsecretsh",
      type: "configmap",
    },

    // Init.
    {
      file: "jobs/init.yaml.j2",
      template: (importstr "templates/jobs/init.yaml.j2"),
      name: "nova-init",
      type: "job",
    },

    {
      file: "jobs/db-sync.yaml.j2",
      template: (importstr "templates/jobs/db-sync.yaml.j2"),
      name: "nova-db-sync",
      type: "job",
    },

    {
      file: "jobs/post.yaml.j2",
      template: (importstr "templates/jobs/post.yaml.j2"),
      name: "nova-post",
      type: "job",
    },

    // Deployments.
    {
      file: "api/deployment.yaml.j2",
      template: (importstr "templates/api/deployment.yaml.j2"),
      name: "nova-api",
      type: "deployment",
    },

    {
      file: "auxiliary/conductor.yaml.j2",
      template: (importstr "templates/auxiliary/conductor.yaml.j2"),
      name: "nova-conductor",
      type: "deployment",
    },

    {
      file: "auxiliary/scheduler.yaml.j2",
      template: (importstr "templates/auxiliary/scheduler.yaml.j2"),
      name: "nova-scheduler",
      type: "deployment",
    },

    {
      file: "auxiliary/consoleauth.yaml.j2",
      template: (importstr "templates/auxiliary/consoleauth.yaml.j2"),
      name: "nova-consoleauth",
      type: "deployment",
    },

    {
      file: "novncproxy/deployment.yaml.j2",
      template: (importstr "templates/novncproxy/deployment.yaml.j2"),
      name: "nova-novncproxy",
      type: "deployment",
    },

    // Daemonsets.
    {
      file: "compute/compute.yaml.j2",
      template: (importstr "templates/compute/compute.yaml.j2"),
      name: "nova-compute",
      type: "daemonset",
    },

    {
      file: "compute/libvirt.yaml.j2",
      template: (importstr "templates/compute/libvirt.yaml.j2"),
      name: "nova-libvirt",
      type: "daemonset",
    },

    {
      file: "compute/drain.yaml.j2",
      template: (importstr "templates/compute/drain.yaml.j2"),
      name: "nova-drain",
      type: "daemonset",
    },

    // Services.
    {
      file: "api/service.yaml.j2",
      template: (importstr "templates/api/service.yaml.j2"),
      name: "nova-api",
      type: "service",
    },

    {
      file: "novncproxy/service.yaml.j2",
      template: (importstr "templates/novncproxy/service.yaml.j2"),
      name: "nova-novncproxy",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "api/ingress.yaml.j2",
        template: (importstr "templates/api/ingress.yaml.j2"),
        name: "nova-api",
        type: "ingress",
      },

    if $.variables.network.ingress.enabled == true then
      {
        file: "novncproxy/ingress.yaml.j2",
        template: (importstr "templates/novncproxy/ingress.yaml.j2"),
        name: "nova-novncproxy",
        type: "ingress",
      },
  ],

  deploy: [
    {
      name: "$self",
    },
  ]
}, params)
