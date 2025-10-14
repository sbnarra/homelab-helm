#!/bin/bash
set -e

# cd $(dirname $0) && hl-helmfile apply

kubectl delete job backup-test -n system || true
kubectl create job --from=cronjob/backup backup-test -n system

sleep 2
kubectl get po -n system

sleep 3

pod=$(kubectl get po --no-headers -n system | awk '{print $1}' | grep backup-test)
kubectl logs -f $pod -n system
