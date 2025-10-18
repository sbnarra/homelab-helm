from lib import data, context, job, env
from backup import nodes

def backup(all_nodes, backup_nodes, tag):
  if env.as_bool(f"SKIP_{tag.replace("-", "_").upper()}"): return

  ctx = context.Context("directory", tag)
  tagged_nodes = nodes.find(ctx, all_nodes, tag)
  if not tagged_nodes:
    ctx.throw(f"no nodes tagged data/{tag}=1")
  elif len(tagged_nodes) > 1:
    ctx.throw(f"multiple nodes tagged data/{tag}=1: {tagged_nodes}")
  tagged_node = next(iter(tagged_nodes), None)

  potential_backup_nodes = [backup_node for backup_node in backup_nodes if backup_node != tagged_node]
  backup_node = potential_backup_nodes[0] if potential_backup_nodes else None
  backup_distribution_nodes = [potential_backup_node for potential_backup_node in potential_backup_nodes if potential_backup_node != backup_node]

  ctx = context.Context(tagged_node, tag)
  if not backup_node:
    ctx.throw(f"unable to backup {tag} directory, no backup node: node={ctx.node},potential_backup_nodes={potential_backup_nodes}")
  job.queue(ctx, _sync, ctx, tag, tagged_node, backup_node, backup_distribution_nodes)

def _sync(ctx, tag, tagged_node, backup_node, backup_distribution_nodes):
  path = f"/lab/{tag}"
  data.sync(ctx, tagged_node, path, backup_node, path)
  for backup_distribution_node in backup_distribution_nodes:
    job.queue(ctx, data.sync, ctx, backup_node, path, backup_distribution_node, path)
