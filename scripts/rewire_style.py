#!/usr/bin/env python3
"""
Rewrite external tile URLs in a Mapbox/MapLibre style to point at a local tileserver-gl endpoint.

Usage examples:
  # Fetch original style from the project's GitHub and rewrite tiles to use india-latest MBTiles
  python3 scripts/rewire_style.py --output web/local1-versatiles/colorful_style_local.json \
      --mapping '{"versatiles-shortbread": "india-latest"}' --port 8080

  # Rewrite an existing style file and provide a mapping file
  python3 scripts/rewire_style.py --input web/local1-versatiles/colorful_style.json \
      --output web/local1-versatiles/colorful_style_local.json --mapping-file mappings.json --port 8080

The script replaces all entries in each source's `tiles` array with a single local template
in the form http://localhost:{port}/data/{mbtiles_basename}/{z}/{x}/{y}.pbf where the
mbtiles_basename is provided in the mapping (source_name -> mbtiles basename w/o .mbtiles).
If no mapping is supplied for a source that contains remote tiles, the script will leave that
source unchanged but will print a warning.
"""
import argparse
import json
import os
import re
import sys
from urllib.request import urlopen

DEFAULT_REMOTE_STYLE_URL = "https://raw.githubusercontent.com/answerquest/india-vector-maps/main/local1-versatiles/colorful_style.json"


def load_json_from_url(url):
    with urlopen(url) as r:
        return json.load(r)


def load_json_from_file(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', '-i', help='Path to input style JSON. If omitted the script fetches the original style from the upstream repo.')
    p.add_argument('--output', '-o', required=True, help='Output style JSON path')
    p.add_argument('--mapping', '-m', help='JSON string mapping sourceName -> mbtiles_basename (no .mbtiles)')
    p.add_argument('--mapping-file', '-f', help='JSON file containing the mapping')
    p.add_argument('--port', type=int, default=8080, help='Tileserver port used in generated URLs')
    args = p.parse_args()

    if args.mapping and args.mapping_file:
        print('Please provide either --mapping or --mapping-file, not both', file=sys.stderr)
        sys.exit(2)

    mapping = {}
    if args.mapping:
        mapping = json.loads(args.mapping)
    elif args.mapping_file:
        mapping = load_json_from_file(args.mapping_file)

    # Load style
    if args.input:
        style = load_json_from_file(args.input)
    else:
        print('Fetching original style from', DEFAULT_REMOTE_STYLE_URL)
        style = load_json_from_url(DEFAULT_REMOTE_STYLE_URL)

    replaced = []
    warnings = []

    for source_name, source in list(style.get('sources', {}).items()):
        # Only process vector tile sources that define 'tiles'
        if isinstance(source, dict) and 'tiles' in source and isinstance(source['tiles'], list):
            # look for remote urls (http/https)
            any_remote = any(isinstance(t, str) and re.match(r'^https?://', t) for t in source['tiles'])
            if not any_remote:
                continue

            mbname = mapping.get(source_name)
            if not mbname:
                # try heuristic: if source defines a 'name' or attribution including a hint
                warnings.append(f"No mapping provided for source '{source_name}' — leaving tiles unchanged")
                continue

            # Construct local tiles url template
            local_template = f"http://localhost:{args.port}/data/{mbname}/{{z}}/{{x}}/{{y}}.pbf"
            source['tiles'] = [local_template]
            # prefer xyz scheme
            source['scheme'] = source.get('scheme', 'xyz')
            replaced.append(source_name)

    if replaced:
        print('Rewrote tile URLs for sources:', ', '.join(replaced))
    if warnings:
        for w in warnings:
            print('WARNING:', w, file=sys.stderr)

    # Save output
    save_json(style, args.output)
    print('Wrote modified style to', args.output)


if __name__ == '__main__':
    main()
