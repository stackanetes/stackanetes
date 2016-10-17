local kpm = import "kpm.libjsonnet";

function(
   params={}
)

local result = kpm.package({
      package: {
         name: "stackanetes/etcd",
         expander: "jinja2",
         author: "Antoine Legrand",
         version: "3.0.6-1",
         description: "etcd",
         license: "MIT",
      },

      variables: {
        control_node_label: "openstack-control-plane",
        env: 'redis',
         image: "quay.io/coreos/etcd:v3.0.6",
         cluster_token: "etcd-stackanetes-1",
         cluster_state: "'new'",
         service: "svc.cluster.local",
         data_volumes: [
            { name: "varetcd",
              emptyDir: {
               medium: "" },
            },
         ],
      },

      resources:
         [{ file: "etcd-member-dp.yaml",
            name: "etcd",
            type: "deployment",
            sharded: "etcd",
            template:: (importstr "templates/etcd-member-dp.yaml"),
          },

          { file: "etcd-member-svc.yaml",
            name: "etcd",
            type: "svc",
            sharded: "etcd",
            template:: (importstr "templates/etcd-member-svc.yaml"),
          },
          { file: "etcd-svc.yaml",
            name: "etcd",
            type: "svc",
            template:: (importstr "templates/etcd-svc.yaml"),
          },
         ],

      shards: {
         etcd: 3,
      },

      deploy: [
        { name: "$self"},
        ]
   }, params);

result
