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

One-command deploy (including demo site)

To perform a single command deploy that prepares MBTiles, generates a local style that mirrors the upstream style with local tile URLs, deploys the tileserver, and serves the demo web page via nginx, run:

ansible-playbook -i inventory.ini ansible/playbook.yml --become

After the play completes, open your browser to http://<target-host>/map2.html to view the demo. The playbook:
- creates a persistent MBTiles directory on the target host
- mounts a RAM disk and copies MBTiles into it
- installs tileserver-gl and starts it as a systemd service
- generates a local copy of the upstream style (rewrites remote tiles to point to local /data/<mbtiles>/... endpoints)
- installs and configures nginx to serve `/var/lib/tileserver/web` so `map2.html` and the generated style are available via HTTP

Boundary layers and styling

The style generation rewrites the upstream style (the colorful versatiles style from the link you provided) and keeps its layers — including the boundary layers for country and state (admin_level 2 and 4). The `style_source_mapping` default maps the `versatiles-shortbread` source to the `india-latest` MBTiles so that political boundary rendering from the original style is preserved when served locally. If you want to change which MBTiles file powers which style source, update the `style_source_mapping` variable in `ansible/roles/tileserver/defaults/main.yml` or pass an override variable during the playbook execution.

Cloudflare Tunnel (cloudflared) — keys, setup and secure handling

What credentials/permissions are needed
- No secret credentials are required just to run the local tileserver and the role if you only want to use the existing tunnel and add a path-based ingress rule. The role can optionally (and safely) update an existing local cloudflared config file at `/etc/cloudflared/config.yml` to add a new ingress rule.
- If you want the role to create DNS entries or automate Cloudflare-managed hostnames, you will need a Cloudflare API Token with scoped permissions. Recommended minimal scopes for DNS management:
  - Zone.Zone:Read (to list the zone)
  - Zone.DNS:Edit (to create/update DNS records)
  - (If automating tunnels via the API you may need additional permissions; consult Cloudflare docs.)

Minimum CF API token permissions for automated DNS creation (if you choose to use it):
- Permissions: `Zone:Read`, `Zone:DNS:Edit` scoped to the target zone.

Where to set credentials and how to provide them to Ansible securely
- Do NOT place API tokens or private tunnel credential files in the repository.
- Options to supply secrets safely:
  1) Ansible Vault: store sensitive variables in an encrypted vault file and reference them in inventory or group_vars. Example:
     ansible-vault create group_vars/tileserver/vault.yml
     (store: cloudflare_api_token: "<YOUR_TOKEN>")
     Then run playbook with `--ask-vault-pass` or supply vault password file.
  2) Environment variables + extra-vars: export CF_API_TOKEN in your shell and pass as extra-vars when invoking the playbook: 
     export CF_API_TOKEN="abcdefgh123..."
     ansible-playbook -i inventory.ini ansible/playbook.yml --become -e "cloudflare_api_token=$CF_API_TOKEN"
  3) CI/CD secrets store: store tokens in your CI secrets (GitHub Actions secrets, GitLab CI variables) and pass them into the job at runtime; never store tokens in plaintext in the repo.

How the role uses the tunnel (reuse existing tunnel)
- The role will NOT create a new Cloudflare Tunnel by default. Instead it will:
  - Copy a small safe merge script (`scripts/merge_cloudflared_ingress.py`) to the target host,
  - Install PyYAML (`python3-yaml`) so the merge script can safely parse and update `/etc/cloudflared/config.yml`,
  - Add either a hostname-based or path-based ingress rule depending on the variables you set:
    - Hostname: set `cloudflared_ingress_hostname: 'tiles.example.com'` to add a hostname rule.
    - Path: leave `cloudflared_ingress_hostname` empty and set `cloudflared_ingress_path: '/data/*'` to add a path rule on the existing hostname.
  - The merge script makes a timestamped backup before altering the YAML and prints `MODIFIED` or `UNCHANGED`. If the rule already exists, no change is made.
- If you do not want Ansible to modify your cloudflared configuration, set `cloudflared_update_ingress: false`. The role will still generate and copy the style file; you can then add the ingress rule manually.

Embedding the public tiles URL into the style
- To have the generated style reference the public tunnel URL, set the `cloudflared_tiles_base_url` variable. Examples:
  - Hostname-based ingress: `cloudflared_tiles_base_url: 'https://tiles.example.com/data/{mbtiles}'`
  - Path-based reuse of existing hostname: `cloudflared_tiles_base_url: 'https://your-existing-host.example.com/data'`
- The rewriter supports a `{mbtiles}` token — if present it will be replaced by the MBTiles basename; if missing it will append the MBTiles basename automatically.

Example secure workflow (path-based reuse of existing tunnel)
1. On your control machine, generate the local style and tell the role to use the existing tunnel path and not alter DNS:
   ansible-playbook -i inventory.ini ansible/playbook.yml --become -e "cloudflared_update_ingress=true cloudflared_ingress_path='/data/*' cloudflared_tiles_base_url='https://your-existing-host.example.com/data'"
2. The role will add an ingress `/data/*` rule to your existing tunnel config (with a safe backup), copy the style, and restart cloudflared if needed.

What the role will NOT do unless you enable more automation
- The role will NOT create Cloudflare API tokens, tunnel credentials, or DNS records for you unless you explicitly add automation for DNS or tunnel creation. Those steps require elevated Cloudflare permissions and are intentionally not automated by default.

Secret scan confirmation
- I scanned the repository for common secret names and patterns (API tokens, zone IDs, account IDs, `api_token`, `api_key`, `secret`, and long alphanumeric sequences) and did not find any Cloudflare API tokens, keys, or secret files committed to the repository.
- Please double-check that you have not accidentally placed any secret tokens in files you plan to commit. If you want, I can add a pre-commit hook to detect common secret patterns.

Do NOT commit credentials
- If you add any Cloudflare API tokens or other secrets to inventory or group_vars during testing, always encrypt them with Ansible Vault or keep them out of the repo and use environment variables or your CI secret store.

If you want help with DNS automation
- I can add optional Ansible tasks that call the Cloudflare API to create DNS records for new hostnames (this requires a Cloudflare API token and zone ID). If you want that, tell me and I will add a secure, optional task that accepts your API token via Ansible Vault or environment variable and creates the required DNS record.
