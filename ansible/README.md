Tileserver-GL Ansible setup

What this playbook does:
- Installs runtime dependencies (Node.js, npm, rsync)
- Creates a persistent MBTiles directory (/var/lib/tileserver/mbtiles)
- Creates and mounts a RAM disk (tmpfs) at /mnt/tileserver-mbtiles
- Copies MBTiles from the repository into the persistent directory and rsyncs into RAM disk
- Installs tileserver-gl globally via npm and deploys a systemd service that syncs MBTiles to RAM disk before starting tileserver

Quick start (control machine must have access to target host via SSH and have Ansible installed):

1. Inventory example (save as inventory.ini):

[tileserver]
myserver.example.com ansible_user=ubuntu

2. Run the playbook:

ansible-playbook -i inventory.ini ansible/playbook.yml --become

Notes and configuration
- The role defaults are in ansible/roles/tileserver/defaults/main.yml. Adjust these values to change mount point or RAM disk size.
- The playbook will try to copy the MBTiles files listed in defaults (absolute paths inside the repo). If you want to provide different MBTiles, either update the variable `mbtiles_files` or place files in the persistent directory on the target at `/var/lib/tileserver/mbtiles`.
- The systemd service `tileserver-ram-sync.service` runs at boot to keep the RAM disk populated from the persistent directory.
- The tileserver systemd service is `tileserver-ram.service` and will start tileserver-gl serving files from the RAM disk at the configured port (default 8080).

map2.html and style
- A sample `web/map2.html` and a simplified `web/local1-versatiles/boundary_style.json` were added. The style references a local vector tile endpoint at `http://localhost:8080/data/india-latest/{z}/{x}/{y}.pbf` — adjust the style's source URLs if your tiles are named differently when served by tileserver-gl.

Caveats
- tmpfs is ephemeral: if the machine reboots, MBTiles are restored from the persistent directory by the sync service.
- Debian/Ubuntu Node/npm packages from official apt repositories can be old; consider using NodeSource if you need a newer Node.js runtime.

Cloudflared (Cloudflare Tunnel) integration

This role can optionally update an existing cloudflared tunnel configuration on the target host to add an ingress rule that routes tile requests to the local tileserver. By default the role will:

- copy a safe merge script (`scripts/merge_cloudflared_ingress.py`) to the target,
- install `python3-yaml` (PyYAML) so the merge script can parse and safely update the YAML config,
- append a hostname- or path-based ingress rule to the existing cloudflared config (backing up the original), and
- restart the `{{ cloudflared_service_name }}` systemd service if the config was modified.

Defaults
- The role looks for the cloudflared config at `{{ cloudflared_config_path }}` (default `/etc/cloudflared/config.yml`).
- Configure `cloudflared_ingress_hostname` (if you want a new hostname like `tiles.example.com`) or leave it empty and the role will add a path-based rule using `cloudflared_ingress_path` (default `/data/*`) on the existing tunnel hostname.
- Remote style generation: set `cloudflared_tiles_base_url` to the public URL you want embedded into the generated style, for example:

  cloudflared_tiles_base_url: 'https://tiles.example.com/data/{mbtiles}'

  If this is set the style rewriter will use it when producing tile URLs. If it's empty the role will default to `http://localhost:{{ tileserver_port }}` and the rewriter will embed localhost-based URLs.

Safety
- The merge script creates a timestamped backup of the cloudflared config before modifying it.
- If the exact same ingress rule already exists the script will not change the config and will print `UNCHANGED`.

Permissions & prerequisites
- The target host should already be running a Cloudflare Tunnel service and the role will attempt to update its configuration. If your environment uses different config paths or a service name other than `{{ cloudflared_service_name }}` update the defaults in `ansible/roles/tileserver/defaults/main.yml`.

Manual alternative
- If you prefer not to let Ansible modify your tunnel config automatically, you can set `cloudflared_update_ingress: false` and manually add the ingress rule (examples are in the repo’s documentation). The generated style can still be created with the base URL set and copied to the target without altering the tunnel.
