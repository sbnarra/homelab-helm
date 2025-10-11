#!/bin/bash
set -e

# cd $(dirname $0) && hl-helmfile apply

kubectl delete job backups-test -n system || true
kubectl create job --from=cronjob/backups backups-test -n system

sleep 2
kubectl get po

sleep 3
pod=$(kubectl get po --no-headers -n system | awk '{print $1}' | grep backups-test)
kubectl logs -f $pod -n system
