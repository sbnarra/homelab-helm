from lib import k8, context, env, data, job

def backup(namespace_nodes, backup_nodes):
  if env.as_bool(f"SKIP_PERSISTENCE"): return
  for namespace, node in namespace_nodes.items():
    ctx = context.Context(node, namespace)
    if env.include_namespace(namespace):
      job.queue(ctx, _backup_namespace, ctx, backup_nodes)
    else: ctx.info(f"excluding namespace")

def _backup_namespace(ctx, backup_nodes):
  for deployment in k8.resource_names(ctx, "deployment", ctx.namespace):
    ctx = context.Context(ctx.node, ctx.namespace, deployment)
    if data.exists(ctx):
      job.queue(ctx, _backup_deployment, ctx, backup_nodes)
      ctx.trace("queued backup")
    else: ctx.debug("no persistence data")

def _backup_deployment(ctx, backup_nodes):
  potential_backup_nodes = [backup_node for backup_node in backup_nodes if backup_node != ctx.node]
  backup_node = potential_backup_nodes[0] if potential_backup_nodes else None
  if not backup_node:
    ctx.throw(f"unable to backup, no primary backup node: node={ctx.node},potential_backup_nodes={potential_backup_nodes}")
  backup_distribution_nodes = [node for node in potential_backup_nodes if node != backup_node]

  path = f"/lab/persistence/{ctx.namespace}/{ctx.deployment}/"
  replicas = k8.scale_down(ctx)
  try: data.sync(ctx, ctx.node, path, backup_node, path)
  finally: job.queue(ctx, k8.scale_up, ctx, replicas)
  for backup_distribution_node in backup_distribution_nodes:
    if backup_node != backup_distribution_node:
      job.queue(ctx, data.sync, ctx, backup_node, path, backup_distribution_node, path)
