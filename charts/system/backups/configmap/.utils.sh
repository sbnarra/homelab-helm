#!/bin/bash
DEBUGGING=0
MAX_CONCURRENT=$((`nproc` * 2))

month=$(date "+%b" | tr '[:upper:]' '[:lower:]')
weekday=$(date "+%a" | tr '[:upper:]' '[:lower:]')
dayofmonth=$(date "+%d")
sync_cmd="rclone sync --transfers $(($MAX_CONCURRENT / 2)) --checkers $MAX_CONCURRENT --multi-thread-streams $(($MAX_CONCURRENT / 2)) --multi-thread-cutoff 60M --progress"

debug() {
  _debugging=
  [ "$DEBUGGING" == "1" ] && _debugging="[DEBUG]"
  _context=
  [ "$CONTEXT" != "" ] && _context="[$CONTEXT]"

  echo "[$(date "+%F %T")]$_debugging$_context: $@"
}

run() {
  debug "running: $@"
  start=`date +%s`

  [ "$DEBUGGING" != "1" ] && $@
  [ "$DEBUGGING" == "1" ] && debug "Exec: $@"

  end=`date +%s`
  took=`_print-duration $((end-start))`
  debug "[$took] $@"
}

run-logged() {
  log=$1; shift

  debug "running: $@ >> $log 2>&1"
  start=`date +%s`

  [ "$DEBUGGING" != "1" ] && $@ >> $log 2>&1

  end=`date +%s`
  took=`_print-duration $((end-start))`
  debug "[$took] $@ >> $log 2>&1"
}

_print-duration() {
  duration=$1
  minutes=$(( (duration % 3600) / 60 ))
  seconds=$((duration % 60))
  [ $minutes -ne 0 ] && echo -n "${minutes}mins "
  echo "${seconds}secs"
}
