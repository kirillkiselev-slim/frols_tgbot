#!/bin/sh

# Start Xvfb
Xvfb :99 -screen 0 1024x768x24 &

# Export display
export DISPLAY=:99

dbus-launch --config-file=/usr/share/dbus-1/system.conf &

# Run mlx
mlx &

sleep 20

# Run the Python script
python /tg_bot/car_check.py
