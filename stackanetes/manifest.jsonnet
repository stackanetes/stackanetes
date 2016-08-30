local kpm = import "kpm.libjsonnet";
local kpmstd = import "kpm-utils.libjsonnet";

function(
  params={}
)

kpm.package({
  package: {
    name: "stackanetes/stackanetes",
    expander: "jinja2",
    author: "Quentin Machu",
    version: "0.1.1",
    description: "stackanetes",
    license: "Apache 2.0",
  },

  variables: kpmstd.yamlLoads(importstr "parameters.yaml"),

  deploy: [{ variables: $.variables} + dependency for dependency in [
    // Data plane.
    { name: "stackanetes/mariadb" },
    { name: "stackanetes/rabbitmq" },
    { name: "stackanetes/memcached" },
    {
      name: "stackanetes/elasticsearch",
      variables: std.mergePatch($.variables, { deployment: { app_label: "searchlight-elasticsearch" } }),
    },

    // OpenStack services.
    { name: "stackanetes/keystone" },
    { name: "stackanetes/glance" },
    if $.variables.ceph.enabled == true then
      { name: "stackanetes/cinder" },
    { name: "stackanetes/nova" },
    { name: "stackanetes/neutron" },
    { name: "stackanetes/horizon" },
    {
      name: "stackanetes/searchlight",
      variables: std.mergePatch($.variables, { elasticsearch: { address: "searchlight-elasticsearch" } }),
    },

    // Utility services.
    if $.variables.network.ingress.enabled == true then
      { name: "stackanetes/traefik" },
  ]]
}, params)
