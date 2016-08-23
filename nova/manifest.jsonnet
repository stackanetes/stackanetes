local kpm = import "kpm.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "quentinm/nova",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.0",
    description: "nova",
    license: "Apache 2.0",
  },

  variables: {
    deployment: {
      node_label: "openstack-control-plane",
      compute_node_label: "openstack-compute-node",

      replicas: 1,

      image: {
        base: "quay.io/stackanetes/stackanetes-%s:barcelona",

        init: $.variables.deployment.image.base % "kolla-toolbox",
        db_sync: $.variables.deployment.image.base % "nova-api",
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

      dns:  {
        ip: "10.3.0.10",
        domain: "cluster.local",
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
      auth: "{'auth_url':'%s', 'username':'%s','password':'%s','project_name':'%s','domain_name':'default'}" % [$.variables.keystone.auth_url, $.variables.keystone.admin_user, $.variables.keystone.admin_password, $.variables.keystone.admin_project_name],

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
    },

    rados_gateway: {
      enabled: true,
      ceph_admin_keyring: "",
      secret_uuid: "",
      cinder_user: "cinder",
      nova_pool: "vms",
    },

    glance: {
      api_url: "http://glance-api:9292",
    },

    neutron: {
      api_url: "http://neutron-api:9696",
      metadata_secret: "password",
    },

    misc: {
      debug: false,
      workers: 8,
    },
  },

  resources: [
    // Config maps.
    {
      file: "configmaps/init.sh.yaml",
      template: (importstr "templates/configmaps/init.sh.yaml"),
      name: "nova-initsh",
      type: "configmap",
    },

    {
      file: "configmaps/db-sync.sh.yaml",
      template: (importstr "templates/configmaps/db-sync.sh.yaml"),
      name: "nova-dbsyncsh",
      type: "configmap",
    },

    {
      file: "configmaps/post.sh.yaml",
      template: (importstr "templates/configmaps/post.sh.yaml"),
      name: "nova-postsh",
      type: "configmap",
    },

    {
      file: "configmaps/nova.conf.yaml",
      template: (importstr "templates/configmaps/nova.conf.yaml"),
      name: "nova-novaconf",
      type: "configmap",
    },

    {
      file: "configmaps/nova.sh.yaml",
      template: (importstr "templates/configmaps/nova.sh.yaml"),
      name: "nova-novash",
      type: "configmap",
    },

    {
      file: "configmaps/resolv.conf.yaml",
      template: (importstr "templates/configmaps/resolv.conf.yaml"),
      name: "nova-resolvconf",
      type: "configmap",
    },

    {
      file: "configmaps/libvirtd.conf.yaml",
      template: (importstr "templates/configmaps/libvirtd.conf.yaml"),
      name: "nova-libvirtdconf",
      type: "configmap",
    },

    {
      file: "configmaps/ceph.client.admin.keyring.yaml",
      template: (importstr "templates/configmaps/ceph.client.admin.keyring.yaml"),
      name: "nova-cephclientadminkeyring",
      type: "configmap",
    },

    {
      file: "configmaps/ceph.conf.yaml",
      template: (importstr "templates/configmaps/ceph.conf.yaml"),
      name: "nova-cephconf",
      type: "configmap",
    },

    {
      file: "configmaps/libvirt.sh.yaml",
      template: (importstr "templates/configmaps/libvirt.sh.yaml"),
      name: "nova-libvirtsh",
      type: "configmap",
    },

    {
      file: "configmaps/virsh-set-secret.sh.yaml",
      template: (importstr "templates/configmaps/virsh-set-secret.sh.yaml"),
      name: "nova-virshsetsecretsh",
      type: "configmap",
    },

    // Init.
    {
      file: "jobs/init.yaml",
      template: (importstr "templates/jobs/init.yaml"),
      name: "nova-init",
      type: "job",
    },

    {
      file: "jobs/db-sync.yaml",
      template: (importstr "templates/jobs/db-sync.yaml"),
      name: "nova-db-sync",
      type: "job",
    },

    {
      file: "jobs/post.yaml",
      template: (importstr "templates/jobs/post.yaml"),
      name: "nova-post",
      type: "job",
    },

    // Daemons.
    {
      file: "api/deployment.yaml",
      template: (importstr "templates/api/deployment.yaml"),
      name: "nova-api",
      type: "deployment",
    },

    {
      file: "auxiliary/conductor.yaml",
      template: (importstr "templates/auxiliary/conductor.yaml"),
      name: "nova-conductor",
      type: "deployment",
    },

    {
      file: "auxiliary/scheduler.yaml",
      template: (importstr "templates/auxiliary/scheduler.yaml"),
      name: "nova-scheduler",
      type: "deployment",
    },

    {
      file: "auxiliary/consoleauth.yaml",
      template: (importstr "templates/auxiliary/consoleauth.yaml"),
      name: "nova-consoleauth",
      type: "deployment",
    },

    {
      file: "novncproxy/deployment.yaml",
      template: (importstr "templates/novncproxy/deployment.yaml"),
      name: "nova-novncproxy",
      type: "deployment",
    },

    {
      file: "compute/daemonset.yaml",
      template: (importstr "templates/compute/daemonset.yaml"),
      name: "nova-compute",
      type: "daemonset",
    },

    // Services.
    {
      file: "api/service.yaml",
      template: (importstr "templates/api/service.yaml"),
      name: "nova-api",
      type: "service",
    },

    {
      file: "novncproxy/service.yaml",
      template: (importstr "templates/novncproxy/service.yaml"),
      name: "nova-novncproxy",
      type: "service",
    },

    // Ingresses.
    if $.variables.network.ingress.enabled == true then
      {
        file: "api/ingress.yaml",
        template: (importstr "templates/api/ingress.yaml"),
        name: "nova-api",
        type: "ingress",
      },

    if $.variables.network.ingress.enabled == true then
      {
        file: "novncproxy/ingress.yaml",
        template: (importstr "templates/novncproxy/ingress.yaml"),
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
