Quick Start
===================================================
A) Local Deployment (Development/Testing)
  Prerequisites
  No manual prerequisites — the Ansible role will install and configure `nginx`, `docker`, and TileServer-GL automatically.
  
  No Cloudflare Tunnel required
  
  Process:
  1. Place MBTiles files in the repository root (they will be copied to `/var/lib/tileserver/mbtiles`)
  
  2. Configure `config.json` for TileServer-GL according to https://tileserver.readthedocs.io/en/latest/config.html
     Example:
     ```json
     {
       "options": {
         "paths": {
           "fonts": "fonts",
           "styles": "styles"
         }
       },
       "styles": {
         "your-style": {
           "style": "your-style-directory/style.json"
         }
       },
       "data": {
         "your-data": {
           "mbtiles": "your-mbtiles-file.mbtiles"
         }
       }
     }
     ```
  
  3. Configure `inventory.ini` (copy from `inventory.ini.sample`):
     ```ini
     [tileserver]
     localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
     
     [tileserver:vars]
     config_json_path=config.json
     use_config_json_styles=true
     tileserver_nginx_listen=127.0.0.1:8081
     ```
  
  4. Run the playbook:
     ```bash
     ansible-playbook -i inventory.ini ansible/playbook.yml --ask-become-pass
     ```
  
  5. Access the demo:
     - Demo page: http://localhost:8081/map.html (if using custom port)
     - Tile API: http://localhost:8081/data/v3/{z}/{x}/{y}.pbf

  B) Remote / public deployment (Cloudflare Tunnel)
  Prerequisites on target server:
  - `cloudflared` installed and a tunnel already configured (the role can *update* an existing config; it does not create tunnels)
  - MBTiles present in the repository or target host
  - `config.json` configured for TileServer-GL
  
  Process:
  1. Place MBTiles files in the repository root
  
  2. Configure `config.json` for TileServer-GL (see TileServer-GL documentation)
  
  3. Configure `inventory.ini` for remote host with Cloudflare settings:
     ```ini
     [tileserver]
     your-remote-host ansible_user=ubuntu
     
     [tileserver:vars]
     config_json_path=config.json
     use_config_json_styles=true
     cloudflared_update_ingress=true
     cloudflared_ingress_hostname=your-tileserver-domain.com
     cloudflared_ingress_path=/data/*
     cloudflared_tiles_base_url=https://your-tileserver-domain.com/data
     tileserver_nginx_listen=127.0.0.1:8081
     ```
  
  4. Run the playbook:
     ```bash
     ansible-playbook -i inventory.ini ansible/playbook.yml --ask-become-pass
     ```
  
  5. Access via your Cloudflare tunnel hostname

  Configuration
  - `config.json`: Configure TileServer-GL according to https://tileserver.readthedocs.io/en/latest/config.html
  - `inventory.ini`: Set deployment variables (nginx port, Cloudflare settings, etc.)
  - The Ansible role reads from these files and deploys automatically
  
  Style and data management
  - Place style JSON files in `styles/{style-name}/style.json`
  - Place MBTiles files in repository root
  - Configure sources in `config.json` using `mbtiles://{source-name}` references
  - Ansible automatically copies sprites, fonts, and styles to the correct locations

  Troubleshooting
  - If demo shows only controls and no map features:
    - Open browser DevTools → Network and Console
    - Verify the style JSON loads: `/styles/{style-name}/style.json`
    - Verify tiles load: `/data/v3/{z}/{x}/{y}.pbf`
    - Check that `config.json` sources use `mbtiles://{source-name}` format
    - Ensure MBTiles files are in the repository root
  
  - If Cloudflare hostname returns 404:
    - Verify `cloudflared_update_ingress=true` and config file exists at `/etc/cloudflared/config.yml`
    - Check that ingress rules were added correctly
  
  - If fonts or sprites don't load:
    - Ensure style files are in `styles/{style-name}/` directory
    - Check that sprite files exist in `styles/{style-name}/sprite*.png` and `sprite*.json`

  Security
  - The merge script makes a backup before changing `/etc/cloudflared/config.yml`. If you prefer not to let Ansible edit your tunnel, set `cloudflared_update_ingress: false` and apply ingress rules manually.

  Credits & notes
  - The role defaults to Docker deployment to avoid native Node/npm dependency issues. Set `tileserver_deploy_method: native` in your inventory if you specifically want the npm-based install.
