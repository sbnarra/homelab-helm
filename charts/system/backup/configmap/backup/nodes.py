from lib import k8

def namespace(ctx):
  all_nodes = set()
  namespace_nodes = dict()

  for namespace in k8.resource_names(ctx, "namespace"):
    node_ip = k8.pv_node_ip(ctx, namespace)
    if not node_ip: 
      ctx.info(f"no persitence node found for namespace '{namespace}'")
      continue
    all_nodes.add(node_ip)
    namespace_nodes[namespace] = node_ip

  ctx.debug(f"all_nodes={all_nodes}")
  ctx.debug(f"namespace_nodes={namespace_nodes}")
  return (all_nodes, namespace_nodes)

def find(ctx, all_nodes, tag):
  found = set()
  for node_ip in all_nodes:
    if k8.get_nodes_by_label(ctx, {"data/host": node_ip, f"data/{tag}": 1}):
      found.add(node_ip)
  return found
