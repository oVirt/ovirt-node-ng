#
# Minimal kickstart example for a manual ovirt-node-ng installation
# Use LVM Thin and use the liveimg source
#

liveimg --url=URL_TO_SQUASHFS

# FIXME This should be fixed more elegantly with
# https://bugzilla.redhat.com/663099#c14
# This only works with the Node installer for now
autopart --type=thinp

%post --erroronfail
imgbase layout --init
%end

