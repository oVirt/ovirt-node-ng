#
# Minimal kickstart example for a manual ovirt-node-ng installation
# Use LVM Thin and use the liveimg source
#

autopart --type=thinp --fstype=ext4
liveimg --url=http://jenkins.ovirt.org/job/ovirt-node-ng_master_build-artifacts-fc22-x86_64/lastStableBuild/artifact/exported-artifacts/rootfs:org.ovirt.Node.Next:x86_64:0.squashfs.img
