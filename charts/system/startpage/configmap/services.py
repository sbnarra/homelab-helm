#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
import subprocess
import json
import os

def run_kubectl_command(args):
    try:
        result = subprocess.run(
            ['kubectl'] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running kubectl: {e.stderr}", file=sys.stderr)
        return None

def get_all_ingresses():
    output = run_kubectl_command(['get', 'ingress', '-A', '-o', 'json'])
    if not output:
        return []
    data = json.loads(output)
    return data.get('items', [])

def extract_service_from_ingress(ingress):
    metadata = ingress.get('metadata', {})
    spec = ingress.get('spec', {})
    annotations = metadata.get('annotations', {})
    labels = metadata.get('labels', {})

    namespace = metadata.get('namespace', '...')
    name = metadata.get('name', 'Unknown')

    # Get the first host from rules
    rules = spec.get('rules', [])
    url = rules[0].get('host', '') if rules else ''

    icon = labels.get('startpage/icon', 'link')
    protocol = labels.get('startpage/protocol', 'https')

    return {
        'namespace': namespace,
        'name': name,
        'url': url,
        'icon': icon,
        'protocol': protocol
    }

def load_local_services():
    """Load services from local services.json file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    services_file = os.path.join(script_dir, 'services.json')
    
    if not os.path.exists(services_file):
        return []
    
    try:
        with open(services_file, 'r') as f:
            data = json.load(f)
            return data.get('services', [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading services.json: {e}", file=sys.stderr)
        return []

def get_services_from_kubectl():
    ingresses = get_all_ingresses()
    if not ingresses:
        kubectl_services = []
    else:
        kubectl_services = []
        for ingress in ingresses:
            service = extract_service_from_ingress(ingress)
            kubectl_services.append(service)
    
    # Load local services
    local_services = load_local_services()
    
    # Merge: local services + kubectl services
    all_services = local_services + kubectl_services
    
    # Sort by namespace, then by name
    all_services.sort(key=lambda x: (x['namespace'], x['name']))
    
    return {'services': all_services}

def main():
    result = get_services_from_kubectl()
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()