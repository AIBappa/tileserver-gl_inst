#!/usr/bin/env python3
"""
Merge a new ingress rule into an existing cloudflared YAML config safely.
Requires PyYAML (python3-yaml) installed.

Usage:
  merge_cloudflared_ingress.py --config /etc/cloudflared/config.yml --hostname tiles.example.com --service http://127.0.0.1:8080
  OR
  merge_cloudflared_ingress.py --config /etc/cloudflared/config.yml --path /data/* --service http://127.0.0.1:8080

The script makes a backup of the original config with .bak timestamp suffix before modifying.
It will append the new rule to the ingress list (before the default fallback rule if present).
If the identical rule already exists, no changes are made and the script exits with code 0 and prints 'UNCHANGED'.
If the file was modified, the script prints 'MODIFIED'.
"""
import argparse
import datetime
import os
import sys

try:
    import yaml
except Exception:
    print('This script requires PyYAML (python3-yaml) installed on the target host.', file=sys.stderr)
    sys.exit(2)


def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return yaml.safe_load(fh) or {}


def save_yaml(data, path):
    with open(path, 'w', encoding='utf-8') as fh:
        yaml.safe_dump(data, fh, default_flow_style=False)


def rule_equals(a, b):
    # Compare keys and values for equivalence
    return a == b


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True, help='Path to cloudflared config YAML')
    p.add_argument('--hostname', help='Hostname-based ingress (e.g. tiles.example.com)')
    p.add_argument('--path', help='Path-based ingress (e.g. /data/*)')
    p.add_argument('--service', required=True, help='Local service URL to route to (e.g. http://127.0.0.1:8080)')
    args = p.parse_args()

    cfg_path = args.config
    if not os.path.exists(cfg_path):
        print(f'Config file {cfg_path} does not exist', file=sys.stderr)
        sys.exit(3)

    cfg = load_yaml(cfg_path)
    ingress = cfg.get('ingress')
    if ingress is None:
        ingress = []

    # Build new rule
    new_rule = {'service': args.service}
    if args.hostname:
        new_rule['hostname'] = args.hostname
    if args.path:
        # cloudflared uses 'path' for path matching
        new_rule['path'] = args.path

    # Check for identical rule
    for r in ingress:
        if rule_equals(r, new_rule):
            print('UNCHANGED')
            sys.exit(0)

    # Insert before fallback (service: http_status:404) if present
    fallback_index = None
    for idx, r in enumerate(ingress):
        if isinstance(r, dict) and r.get('service') == 'http_status:404':
            fallback_index = idx
            break

    if fallback_index is None:
        ingress.append(new_rule)
    else:
        ingress.insert(fallback_index, new_rule)

    cfg['ingress'] = ingress

    # Backup
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    bak = cfg_path + '.bak.' + ts
    with open(bak, 'w', encoding='utf-8') as fh:
        yaml.safe_dump(cfg, fh, default_flow_style=False)

    # Write updated config
    save_yaml(cfg, cfg_path)
    print('MODIFIED')
    sys.exit(0)


if __name__ == '__main__':
    main()
