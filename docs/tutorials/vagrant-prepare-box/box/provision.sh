#!/bin/sh -ex
# Provisioning script for the base box:
# We want to have some tools on every VM.

apt-get update
apt-get install -y ca-certificates curl vim

# Allow the root user to log in with the same credentials.
# The tutorial assumes root access.
echo "PermitRootLogin Yes" >> /etc/ssh/sshd_config

mkdir -p /root/.ssh
cp /home/vagrant/.ssh/authorized_keys /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys