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

  // Dependencies' variables result from the ordered merge of:
  // - parameters.yaml (root key)
  // - parameters.yaml (under a key having the same name as the dependency)
  // - variables defined in their deploy's definition
  // The first having the lowest priority and the last the higher.
  parameters: kpmstd.yamlLoads(importstr "parameters.yaml"),
  set_dependency_variables(dependency):: (
    local dep_specific_parameters = if std.objectHas($.parameters, dependency.name) == true then
                                      $.parameters[dependency.name]
                                    else
                                      { };

    local dep_deploy_variables = if std.objectHas(dependency, "variables") then
                                   dependency["variables"]
                                 else
                                   { };

    dependency {
      variables: std.mergePatch($.parameters, std.mergePatch(dep_specific_parameters, dep_deploy_variables)),
    }
  ),

  deploy: [ self.set_dependency_variables(dependency) for dependency in [
    // Data plane.
    { name: "stackanetes/mariadb" },
    { name: "stackanetes/rabbitmq" },
    { name: "stackanetes/memcached" },
    {
      name: "stackanetes/elasticsearch",
      variables: { deployment: { app_label: "searchlight-elasticsearch" } },
    },

    // OpenStack services.
    { name: "stackanetes/keystone" },
    { name: "stackanetes/glance" },
    if $.parameters.ceph.enabled == true then
      { name: "stackanetes/cinder" },
    { name: "stackanetes/nova" },
    { name: "stackanetes/neutron" },
    { name: "stackanetes/horizon" },
    {
      name: "stackanetes/searchlight",
      variables: { elasticsearch: { address: "searchlight-elasticsearch" } },
    },

    // Utility services.
    if $.parameters.network.ingress.enabled == true then
      { name: "stackanetes/traefik" },
  ]]
}, params)
