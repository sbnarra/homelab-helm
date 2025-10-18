# Home Lab Helm

Repo contains helm charts and depends on homelab-deployments to create the kubernetes cluster.

Charts are split into namespaces under ./charts.

These charts are orchestrated using helmfile.

## New Namespace

Adding a new namespace requires persistence to be setup in homelab-deployments before hand.

Once done, add the new namespace to namespace_persistence in ./config/*/values.yaml.

Add new namespace and namespace helmfile into ./charts, then update the root helmfile to reference the new namespace.

Now new deployments can be added.
