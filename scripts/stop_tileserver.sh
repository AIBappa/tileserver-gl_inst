#!/bin/bash
# Stop TileServer-GL container and disable restarts
# This script stops the TileServer-GL Docker container and systemd service

CONTAINER_NAME="tileserver-gl"
SERVICE_NAME="tileserver-ram"

echo "Stopping TileServer-GL container and service..."

# Stop the systemd service first (this will stop the container gracefully)
sudo systemctl stop $SERVICE_NAME 2>/dev/null || echo "Systemd service not running or failed to stop"

# Disable the service to prevent auto-restart
sudo systemctl disable $SERVICE_NAME 2>/dev/null || echo "Failed to disable systemd service"

# Stop and remove Docker container (in case systemd didn't handle it)
docker stop $CONTAINER_NAME 2>/dev/null || echo "Container not running"
docker rm $CONTAINER_NAME 2>/dev/null || echo "Container not found or already removed"

# Disable Docker restarts if container still exists
docker update --restart=no $CONTAINER_NAME 2>/dev/null || echo "Failed to update restart policy"

echo "TileServer-GL stopped and disabled."
echo "To restart, run: sudo systemctl enable $SERVICE_NAME && sudo systemctl start $SERVICE_NAME"