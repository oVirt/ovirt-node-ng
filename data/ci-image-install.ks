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

# FIXME This should be fixed more elegantly with https://bugzilla.redhat.com/663099#c14
# At best we could use: autopart --type=thinp
reqpart --add-boot
part pv.01 --size=42000 --grow
volgroup HostVG pv.01
logvol swap --vgname=HostVG --name=swap --fstype=swap --recommended
logvol none --vgname=HostVG --name=HostPool --thinpool --size=40000 --grow
logvol /    --vgname=HostVG --name=root --thin --poolname=HostPool --fsoptions="defaults,discard" --size=6000
logvol /var --vgname=HostVG --name=var --thin --poolname=HostPool --fsoptions="defaults,discard" --size=15000

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
set -x
imgbase --debug layout --init
%end
