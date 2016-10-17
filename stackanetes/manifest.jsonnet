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
  variables: kpmstd.yamlLoads(importstr "parameters.yaml"),
  set_dependency_variables(dependency):: (
    local dep_specific_parameters = if std.objectHas($.variables, dependency.name) == true then
                                      $.variables[dependency.name]
                                    else
                                      { };

    local dep_deploy_variables = if std.objectHas(dependency, "variables") then
                                   dependency["variables"]
                                 else
                                   { };

    dependency {
      variables: std.mergePatch($.variables, std.mergePatch(dep_specific_parameters, dep_deploy_variables)),
    }
  ),

  deploy: [ self.set_dependency_variables(dependency) for dependency in kpmstd.compact([
    // Data plane.
    { name: "stackanetes/mariadb" },
    { name: "stackanetes/rabbitmq" },
    { name: "stackanetes/memcached" },
    { name: "stackanetes/etcd" },
    {
      name: "stackanetes/elasticsearch",
      variables: { deployment: { app_label: "searchlight-es" } },
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
      variables: { elasticsearch: { address: "searchlight-es" } },
    },

    // Utility services.
    if $.variables.network.ingress.enabled == true then
      { name: "stackanetes/traefik" },
  ])]
}, params)
