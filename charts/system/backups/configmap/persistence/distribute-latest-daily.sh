#!/bin/bash
. $(dirname $0)/../.utils.sh

distribute-lastest-daily() {
  _sync-lastest-daily pi daily &
  if [ $dayofmonth -eq 1 ]; then
    _sync-lastest-daily nas monthly &
    _sync-lastest-daily pi monthly &
  fi
  wait
}

_sync-lastest-daily() {
  host=$1
  schedule=$2 # daily/monthly

  backup_root=/lab/$host/backups/persistence
  CONTEXT="$host/$schedule" run mkdir -p $backup_root/logs

  CONTEXT="$host/$schedule" run-logged $backup_root/logs/$(date "+%Y-%m-%d_%H-%M-%S").log \
    $sync_cmd \
      /lab/nas/backups/persistence/daily/$weekday/ \
      $backup_root/$schedule
}

distribute-lastest-daily
