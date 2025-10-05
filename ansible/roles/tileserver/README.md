Tileserver role

This role installs and configures a tileserver-gl instance and mounts MBTiles on a RAM disk.

## Deployment modes

By default the role launches the upstream `maptiler/tileserver-gl` container via systemd while still preparing the RAM disk and syncing MBTiles into it. If you prefer the historical native Node.js installation, set `tileserver_deploy_method: native` (for example via inventory or `-e`). The following variables control the Docker flow and live in `defaults/main.yml`:

- `tileserver_deploy_method`: `docker` (default) or `native`
- `tileserver_docker_image`: image reference (defaults to `maptiler/tileserver-gl:v4.5.0`)
- `tileserver_docker_bind_address`: host interface to bind (defaults to `0.0.0.0`)
- `tileserver_docker_extra_args`: optional list of additional arguments passed to `docker run`

When `tileserver_deploy_method` is `native`, the role reinstates the npm-based workflow, including Node.js installation and dependency shims.
