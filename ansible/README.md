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

If you want I can also add an inventory example and a small Ansible role test to validate installation.
