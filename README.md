Quick Start
Local Deployment (Development/Testing)
Prerequisites
nginx installed (sudo apt install nginx)

No Cloudflare Tunnel required

MBTiles files placed in /var/lib/tileserver/mbtiles (default, check within Ansible role or config)

Sample inventory.ini
text
[tileserver]
localhost ansible_connection=local
Run the Playbook
bash
ansible-playbook -i inventory.ini ansible/playbook.yml --ask-become-pass
Typical Access URLs
Default (nginx uses port 80):

Tileserver demo:
http://localhost/map2.html

Tile API:
http://localhost/data/{mbtiles}/{z}/{x}/{y}.pbf

If you set nginx to a custom port (e.g., 8081):

Tileserver demo:
http://localhost:8081/map2.html

Tile API:
http://localhost:8081/data/{mbtiles}/{z}/{x}/{y}.pbf

Note: Browsers use port 80 by default for http:// URLs, so you don’t need to specify :80 in the address. For any other port, you must include it, e.g., http://localhost:8081/.

Remote/Public Deployment (Cloud/Server or Team Access)
Prerequisites
Cloudflare Tunnel running and configured on the remote server

nginx installed on remote server

MBTiles files present in /var/lib/tileserver/mbtiles (on remote)

Sample inventory.ini
text
[tileserver]
your-remote-host ansible_user=YOUR_SSH_USER cf_tunnel_hostname=YOUR_TUNNEL_HOSTNAME
Run the Playbook
bash
ansible-playbook -i inventory.ini ansible/playbook.yml --become
Typical Access URLs
Via Cloudflare Tunnel (public access):

Tileserver demo:
https://YOUR_TUNNEL_HOSTNAME/map2.html

Tile API:
https://YOUR_TUNNEL_HOSTNAME/data/{mbtiles}/{z}/{x}/{y}.pbf

Direct remote access (nginx default port 80):

Tileserver demo:
http://your-remote-host/map2.html

Tile API:
http://your-remote-host/data/{mbtiles}/{z}/{x}/{y}.pbf

If nginx uses a custom port (e.g., 8081):

Tileserver demo:
http://your-remote-host:8081/map2.html

Tile API:
http://your-remote-host:8081/data/{mbtiles}/{z}/{x}/{y}.pbf

Note: :80 is omitted for HTTP URLs when using the default port. Always specify any non-default port in your URL.
