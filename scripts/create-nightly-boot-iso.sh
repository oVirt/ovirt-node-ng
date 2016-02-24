#!/usr/bin/bash

NEWISO=${1:-$(realpath .)/ovirt-node-ng-nightly-boot.iso}

BOOTISO=boot.iso
SQUASHFS=ovirt-node-ng-image.squashfs.img
CLEAN=

cond_curl() {
  if [[ -e "$1" ]]; then echo "Reusing existing $1" ;
  else echo "Fetching $1" ; curl -# -o "$1" $2 ; CLEAN="$CLEAN $1" ; fi
}

echo "Building an oVirt Node Next boot.iso"
echo "from CentOS 7 boot.iso and a nightly squashfs"
echo "This can take a while ..."
cond_curl $BOOTISO http://mirror.centos.org/centos/7/os/x86_64/images/boot.iso
cond_curl $SQUASHFS http://jenkins.ovirt.org/job/ovirt-node-ng_master_build-artifacts-fc22-x86_64/lastStableBuild/artifact/exported-artifacts/ovirt-node-ng-image.squashfs.img

./derive-boot-iso.sh "$BOOTISO" "$SQUASHFS" "$NEWISO"

[[ -n "$CLEAN" ]] && rm $CLEAN

echo "New installation ISO: $NEWISO"
