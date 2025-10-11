#!/bin/bash
. $(dirname $0)/../.utils.sh

current_jobs=0

nas_persistence_path=/lab/nas/persistence
nas_backup_path=/lab/nas/backups/persistence

log_file=$(date "+%Y-%m-%d_%H-%M-%S").log

_item-exist() {
  for i in "${@:2}"; do
    [ "$i" == "$1" ] && return 0
  done
  return 1
}

daily-live-backup() {
  # CONTEXT="nas/daily" run rm -rf $nas_backup_path/daily/$weekday
  CONTEXT="nas/daily" run mkdir -p $nas_backup_path/daily/logs

  skip_backup=(
    # "network/traefik"
    # "tools/vscode"
    "starr/tdarr"
    "system/loki"
    "system/prometheus"
  )

  for namespace in $(ls $nas_persistence_path); do
    for app in $(ls $nas_persistence_path/$namespace); do

      if _item-exist "$namespace/$app" "${skip_backup[@]}"; then
        CONTEXT="$namespace/$app" debug "Skipping Backup"
      else
        _concurrency-wait
        _backup-namespace-app $namespace $app &
        ((current_jobs++))
      fi

    done
  done

  wait
}

_backup-namespace-app() {
  namespace=$1
  app=$2

  # CONTEXT="$namespace/$app" debug "Backup Starting"

  replicas=$(kubectl get deployment $app -n $namespace -o=jsonpath='{.spec.replicas}' 2>/dev/null)
  if [ "$replicas" != "" ]; then
    CONTEXT="$namespace/$app" run kubectl scale --replicas=0 deployment/$app -n $namespace
    _wait-scale-down $namespace $app
  fi

  _sync-dir $namespace $app

  if [ "$replicas" != "" ]; then
    CONTEXT="$namespace/$app" run kubectl scale --replicas=$replicas deployment/$app -n $namespace
  fi

  # CONTEXT="$namespace/$app" debug "Backup Completed"
}

_wait-scale-down() {
  namespace=$1
  app=$2

  duration=1
  pod_count=-1
  while [ "$pod_count" != "0" ]; do

    pod_count=$(kubectl get pods -l=app.kubernetes.io/name=$app -n $namespace --no-headers 2>/dev/null | wc -l)
    [ "$DEBUGGING" == "1" ] && pod_count=0

    if [ "$duration" == "60" ]; then
      CONTEXT="$namespace/$app" debug "scale down timed out after ${duration}s"
      break
    fi

    if [ "$(($duration % 5))" == "0" ]; then
      CONTEXT="$namespace/$app" debug "scale down been waiting for ${duration}s"
    fi

    sleep 1
    ((duration++))
  done
}

_sync-dir() {
  namespace=$1
  app=$2

  CONTEXT="$namespace/$app" run mkdir -p $nas_backup_path/daily/$weekday/$namespace/$app
  CONTEXT="$namespace/$app" run-logged $nas_backup_path/daily/logs/$log_file \
    $sync_cmd \
      $nas_persistence_path/$namespace/$app/ \
      $nas_backup_path/daily/$weekday/$namespace/$app
}

_concurrency-wait() {
  while (( current_jobs >= MAX_CONCURRENT )); do
    # Wait for any background job to finish
    wait -n
    ((current_jobs--))
  done
}

daily-live-backup
