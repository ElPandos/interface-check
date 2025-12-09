#!/bin/bash
set -e

# Take down link
sudo ip link set ens3f0np0 down
sudo ip link set ens3f1np1 down

# Check link is DOWN
echo "Link status after DOWN:"
ip link show | grep ens || true

# Check loaded modules
echo "Loaded mlx5 modules:"
lsmod | grep mlx5 || echo "No mlx5 modules loaded"

# Remove drivers
# RDMA first (if loaded)
sudo modprobe -r mlx5_ib
# Core driver
sudo modprobe -r mlx5_core

# Load driver
sudo modprobe mlx5_core
sudo modprobe mlx5_ib

# Set link UP
sudo ip link set ens3f0np0 up
sudo ip link set ens3f1np1 up

# Check link UP
echo "Link status after UP:"
ip link show | grep ens || true

echo "Driver reload complete"
