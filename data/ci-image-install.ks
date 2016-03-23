#
# CentOS 7.2 compatible kickstart for CI auto-installation
#

lang en_US.UTF-8
keyboard us
timezone --utc Etc/UTC
auth --enableshadow --passalgo=sha512
selinux --permissive
network --bootproto=dhcp --hostname=installed
firstboot --reconfig

rootpw --plaintext ovirt
user --name=ovirt --plaintext --password=ovirt

poweroff

clearpart --all --initlabel --disklabel=gpt
bootloader --timeout=1
autopart --type=thinp --fstype=ext4

#
# The trick is to loop in the squashfs image as a device
# from the host
#
liveimg --url="file:///mnt/livesrc/LiveOS/rootfs.img"

%pre
# Assumption: A virtio device with the serial livesrc is passed, pointing
# to the squashfs on the host.
mkdir -p /mnt/livesrc
mount /dev/disk/by-id/virtio-livesrc /mnt/livesrc
%end

%post
# FIXME maybe the folowing lines can be collapsed
# in future into i.e. "nodectl init"
imgbase layout --init
imgbase --experimental volume --create /var 4G
%end
