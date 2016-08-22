local kpm = import "kpm.libjsonnet";
local kpmstd = import "kpm-utils.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "quentinm/stackanetes",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.1",
    description: "stackanetes",
    license: "Apache 2.0",
  },

  variables: kpmstd.yamlLoads(importstr "parameters.yaml"),

  deploy: [{ variables: $.variables} + dependency for dependency in [
    // Utility services.
    if $.variables.network.ingress.enabled == true then
      { name: "quentinm/traefik" },

    // Data plane.
    { name: "quentinm/mariadb" },
    { name: "quentinm/rabbitmq" },
    { name: "quentinm/memcached" },
    if $.variables.rados_gateway.enabled == true then
      { name: "quentinm/rados-gateway" },

    // OpenStack services.
    { name: "quentinm/keystone" },
    { name: "quentinm/glance" },
    if $.variables.rados_gateway.enabled == true then
      { name: "quentinm/cinder" },
    { name: "quentinm/nova" },
    { name: "quentinm/neutron" },
    { name: "quentinm/horizon" },
  ]]
}, params)
