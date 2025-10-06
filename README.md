Quick Start
===================================================
A) Local Deployment (Development/Testing)
  Prerequisites
  No manual prerequisites — the Ansible role will install and configure `nginx` when deploying the demo/web assets.
  
  No Cloudflare Tunnel required
  
  MBTiles files placed in /var/lib/tileserver/mbtiles (default, check within Ansible role or config)

  # tileserver-gl_inst — quick deploy with RAM-disk + Cloudflare Tunnel

  This project provides an Ansible role and helper scripts to deploy TileServer GL with MBTiles mounted into a RAM disk for fast serving. The role defaults to running TileServer inside Docker to avoid native build issues, but a native npm-based mode is supported.

  Contents
  - ansible/: playbook + role to deploy tileserver, nginx, and optional Cloudflare Tunnel ingress changes
  - web/: demo pages and generated styles
  - scripts/: helpers (style rewriter, cloudflared ingress merge)

  Quick start (local development)
  1. Put MBTiles in the repository (or into the target host persistent dir):

     - Default persistent path on target: `/var/lib/tileserver/mbtiles`

     You can also list MBTiles in `config.json` so the playbook and helper scripts know which files to deploy. Example `config.json` snippet:

     {
       "mbtiles_files": [
         "india-latest.mbtiles",
         "zurich_switzerland.mbtiles"
       ]
     }

  2. Example `inventory.ini` (local host):

    [tileserver]
    localhost ansible_connection=local

  3. Run the playbook (it will prompt for sudo password):

    ansible-playbook -i inventory.ini ansible/playbook.yml --ask-become-pass

  4. After the play finishes, the demo and tile endpoints are available (default nginx port 80):

    - Demo page: http://localhost/map2.html
    - Tile API:   http://localhost/data/{mbtiles}/{z}/{x}/{y}.pbf

    If nginx is bound to a custom port (e.g. 8081): include the port in the URL:

    - Demo: http://localhost:8081/map2.html
    - Tiles: http://localhost:8081/data/{mbtiles}/{z}/{x}/{y}.pbf

  B) Remote / public deployment (Cloudflare Tunnel)
  1. Prerequisites on target server:
    - `cloudflared` installed and a tunnel already configured (the role can *update* an existing config; it does not create tunnels)
    - `nginx` installed (role can install it)
    - MBTiles present in `/var/lib/tileserver/mbtiles`

  2. Example inventory for remote host (replace placeholders):

    [tileserver]
    your-remote-host ansible_user=ubuntu

  3. To update an existing tunnel so `/data/*` or a hostname routes to your tileserver, run the playbook with extra-vars. Example (path-based ingress on an existing hostname):

    ansible-playbook -i inventory.ini ansible/playbook.yml --become -e "cloudflared_update_ingress=true cloudflared_ingress_path='/data/*' cloudflared_tiles_base_url='https://tileserver.example.com/data'"

    Or add a new hostname rule (if you manage that hostname in Cloudflare):

    ansible-playbook -i inventory.ini ansible/playbook.yml --become -e "cloudflared_update_ingress=true cloudflared_ingress_hostname='tileserver.example.com' cloudflared_tiles_base_url='https://tileserver.example.com/data/{mbtiles}'"

  Notes about the Cloudflare merge step
  - The role includes `scripts/merge_cloudflared_ingress.py` which safely edits `/etc/cloudflared/config.yml` (creates a timestamped backup). It requires the tunnel to already exist and a local `config.yml` present.
  - If your tunnel is token-only / managed by Cloudflare without a local config file, the merge script cannot modify cloud configuration — you'll need to add the ingress rule via the Cloudflare dashboard or convert your tunnel to a config-file-managed one.

  Remote MBTiles configuration
  - For remote deployments you can either copy MBTiles into `/var/lib/tileserver/mbtiles` on the target host, or include the filenames in the same `config.json` (deployed/copied by the playbook) so the role can pick them up automatically. The `config.json` approach is helpful for reproducible deployments where the playbook syncs only the MBTiles you list.

  Style generation and local rewrites
  - `scripts/rewire_style.py` rewrites upstream style files to point to local tile URLs. Use `--base-url` to embed a public tunnel URL or `--port` to point to your local tileserver port.

  Examples
  - Generate a local style for OpenMapTiles on port 8080:

    python3 scripts/rewire_style.py --input styles/maptiler-basic/style.json --output web/maptiler-basic_local.json --mapping '{"openmaptiles":"openmaptiles"}' --port 8080

  - Update an existing cloudflared config to add a path ingress to 127.0.0.1:8080:

    python3 scripts/merge_cloudflared_ingress.py --config /etc/cloudflared/config.yml --path '/data/*' --service 'http://127.0.0.1:8080'

  Troubleshooting
  - If demo shows only controls and no map features:
    - Open browser DevTools → Network and Console
    - Verify the style JSON and tiles (`/data/v3/{z}/{x}/{y}.pbf`) load with HTTP 200
    - Ensure the style's `sources` reference the same source-layer names present in your MBTiles (`data.json` lists `vector_layers`)

  - If `cloudflared` public hostname returns 404:
    - Make sure the tunnel config (`/etc/cloudflared/config.yml`) exists and contains the new ingress. The role can add the ingress only if `cloudflared_update_ingress=true` and a config file is present.

  Security
  - The merge script makes a backup before changing `/etc/cloudflared/config.yml`. If you prefer not to let Ansible edit your tunnel, set `cloudflared_update_ingress: false` and apply ingress rules manually.

  Credits & notes
  - The role defaults to Docker deployment to avoid native Node/npm dependency issues. Set `tileserver_deploy_method: native` in your inventory if you specifically want the npm-based install.
