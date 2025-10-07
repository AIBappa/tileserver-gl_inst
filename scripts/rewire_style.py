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
    p.add_argument('--base-url', help="Base URL to prefix tile URLs. Can include the token '{mbtiles}' which will be replaced by the MBTiles basename. Examples:\n  https://tiles.example.com/data/{mbtiles}\n  https://example.com/tiles (will be expanded to https://example.com/tiles/{mbtiles})")
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
            if args.base_url:
                # Use v3 endpoint which works correctly
                base_host = args.base_url.replace('/data', '').rstrip('/')
                local_template = f"{base_host}/data/v3/{{z}}/{{x}}/{{y}}.pbf"
            else:
                local_template = f"http://localhost:{args.port}/data/v3/{{z}}/{{x}}/{{y}}.pbf"
            source['tiles'] = [local_template]
            # prefer xyz scheme
            source['scheme'] = source.get('scheme', 'xyz')
            replaced.append(source_name)

    # Update glyphs and sprite URLs to use local paths
    if args.base_url:
        # Extract the base host from base_url (remove /data suffix if present)
        base_host = args.base_url.replace('/data', '').rstrip('/')
        local_glyphs = f"{base_host}/fonts/{{fontstack}}/{{range}}.pbf"
    else:
        local_glyphs = f"http://localhost:{args.port}/fonts/{{fontstack}}/{{range}}.pbf"
    
    # Update glyphs URL
    if 'glyphs' in style:
        old_glyphs = style['glyphs']
        style['glyphs'] = local_glyphs
        print(f'Updated glyphs URL from {old_glyphs} to {local_glyphs}')

    # Update sprite URLs
    if 'sprite' in style:
        if isinstance(style['sprite'], list):
            for sprite_entry in style['sprite']:
                if isinstance(sprite_entry, dict) and 'url' in sprite_entry:
                    old_sprite = sprite_entry['url']
                    if args.base_url:
                        base_host = args.base_url.replace('/data', '').rstrip('/')
                        sprite_entry['url'] = f"{base_host}/local1-versatiles/basics/sprites@2x"
                    else:
                        sprite_entry['url'] = f"http://localhost:{args.port}/local1-versatiles/basics/sprites@2x"
                    print(f'Updated sprite URL from {old_sprite} to {sprite_entry["url"]}')
        elif isinstance(style['sprite'], str):
            old_sprite = style['sprite']
            if args.base_url:
                base_host = args.base_url.replace('/data', '').rstrip('/')
                style['sprite'] = f"{base_host}/local1-versatiles/basics/sprites@2x"
            else:
                style['sprite'] = f"http://localhost:{args.port}/local1-versatiles/basics/sprites@2x"
            print(f'Updated sprite URL from {old_sprite} to {style["sprite"]}')

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
