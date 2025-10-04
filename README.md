Tileserver-GL with RAM-disk Ansible setup

This repository contains an Ansible role and supporting scripts to run a tileserver-gl instance
with MBTiles mounted in RAM (tmpfs) for speed, while keeping a persistent copy on disk.

Files you will find here
- ansible/playbook.yml: top-level playbook that runs the tileserver role
- ansible/roles/tileserver: Ansible role that prepares a RAM disk, copies MBTiles, installs tileserver-gl, and deploys systemd services
- web/: simple web examples (map2.html and local style directory)
- scripts/rewire_style.py: rewrite external tile URLs in an upstream style JSON to point at your local tileserver endpoints
- scripts/detect_ram_and_set.sh: prints recommended RAM disk size (1/3 of available RAM) e.g. "2048M" or "2G"

Quick usage

1) Rewriting the upstream style to use your local tiles

The role ships with a lightweight example style; if you want to mirror the full original style and
replace the remote tile URLs with your local tileserver endpoints, run the rewire script.

Example: rewrite the upstream style and replace the source "versatiles-shortbread" with your
local MBTiles named "india-latest" (the script will use the server port you supply):

python3 scripts/rewire_style.py --output web/local1-versatiles/colorful_style_local.json \
  --mapping '{"versatiles-shortbread":"india-latest"}' --port 8080

The generated style will reference local vector tile URLs like:
  http://localhost:8080/data/india-latest/{z}/{x}/{y}.pbf

2) Detect and choose a RAM disk size

On the target host you can compute a recommended RAM disk size as one-third of available memory:

# on target
/scripts/detect_ram_and_set.sh

The Ansible role also computes the RAM disk size automatically during the play using Ansible facts
and sets the RAM disk size to 1/3 of available memory. The default variable `ramdisk_size` in
`ansible/roles/tileserver/defaults/main.yml` is used only if the automatic detection is not available.

3) Run the Ansible playbook

Example inventory file (inventory.ini):

[tileserver]
myserver.example.com ansible_user=ubuntu

Run the playbook:

ansible-playbook -i inventory.ini ansible/playbook.yml --become

Notes and caveats
- tmpfs is ephemeral; the role ensures MBTiles are persisted on disk in `/var/lib/tileserver/mbtiles` and a systemd one-shot copies them into the RAM disk at boot.
- The rewire script only replaces `tiles` array entries in the style. If the style references other external resources (glyphs, sprites, tiles from other sources) you may need to adapt the style further.
- Node.js from apt may be older; for newer Node.js use NodeSource or set up a different installation method.

If you want me to integrate the rewire script into the Ansible run (so the style JSON is generated during playbook execution on the control node or the target), I can add that step.
