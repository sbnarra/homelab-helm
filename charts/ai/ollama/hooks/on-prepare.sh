#!/bin/bash

cd ollama
AVIL_HW=$(kubectl get nodes | grep pc && echo gpu || echo cpu)

echo cp hooks/${AVIL_HW}.yaml values.yaml.gotmpl
# cp -a hooks/${AVIL_HW}.yaml values.yaml.gotmpl
