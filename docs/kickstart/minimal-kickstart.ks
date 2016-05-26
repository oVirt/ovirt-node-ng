#
# Minimal kickstart example for a manual ovirt-node-ng installation
# Use LVM Thin and use the liveimg source
#

liveimg --url=URL_TO_SQUASHFS

# FIXME This should be fixed more elegantly with https://bugzilla.redhat.com/663099#c14
# At best we could use: autopart --type=thinp
reqpart --add-boot
part pv.01 --size=42000 --grow
volgroup HostVG pv.01
logvol swap --vgname=HostVG --name=swap --fstype=swap --recommended
logvol none --vgname=HostVG --name=HostPool --thinpool --size=40000 --grow
logvol /    --vgname=HostVG --name=root --thin --poolname=HostPool --fsoptions="discard" --size=6000
logvol /var --vgname=HostVG --name=var --thin --poolname=HostPool --fsoptions="discard" --size=15000

%post --erroronfail
imgbase layout --init
%end

