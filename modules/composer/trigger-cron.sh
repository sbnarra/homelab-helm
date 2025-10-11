#!/bin/bash

NAMESPACE=$1
CRONJOB_NAME=$2
JOB_NAME=$3

usage() {
    echo "$(basename $0) <namespace> <cron-job-name> <job-name>"
    exit 1
}
[ "$NAMESPACE" == "" ] && usage
[ "$CRONJOB_NAME" == "" ] && usage
[ "$JOB_NAME" == "" ] && usage

kubectl -n $NAMESPACE create job --from=cronjob/$CRONJOB_NAME $JOB_NAME
