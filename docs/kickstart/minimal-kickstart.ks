#
# Minimal kickstart example for a manual ovirt-node-ng installation
# Use LVM Thin and use the liveimg source
#

liveimg --url=URL_TO_SQUASHFS

autopart --type=thinp

%post --erroronfail
imgbase layout --init ovirt-node-ng-1.0-0.0
imgbase --experimental volume --create /var 4G
%end

