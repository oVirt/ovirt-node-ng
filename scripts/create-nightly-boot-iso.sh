#!/usr/bin/bash

BRANCH=${BRANCH:-master}
NEWISO=${1:-$(realpath .)/ovirt-node-ng-installer-${BRANCH}-$(date +%Y%m%d).iso}
BOOTISO=${BOOTISO:-boot.iso}
SQUASHFS=${SQUASHFS:-ovirt-node-ng-image.squashfs.img}
DERVICEBOOTISOSCRIPT=${DERVICEBOOTISOSCRIPT:-derive-boot-iso.sh}
CLEAN=

cond_curl() {
  if [[ -e "$1" ]]; then echo "Reusing existing $1" ;
  else echo "Fetching $1 from $2 " ; curl --fail -# -o "$1" $2 ; CLEAN="$CLEAN $1" ; fi
  [[ -n "$3" ]] && $3 $1
}

echo "Building an oVirt Node Next boot.iso"
echo "from CentOS 7 boot.iso and a nightly squashfs"
echo "This can take a while ..."
cond_curl $BOOTISO http://mirror.centos.org/centos/7/os/x86_64/images/boot.iso
cond_curl $SQUASHFS http://jenkins.ovirt.org/job/ovirt-node-ng_${BRANCH}_build-artifacts-fc22-x86_64/lastStableBuild/artifact/exported-artifacts/ovirt-node-ng-image.squashfs.img
cond_curl $DERVICEBOOTISOSCRIPT "https://gerrit.ovirt.org/gitweb?p=ovirt-node-ng.git;a=blob_plain;f=scripts/derive-boot-iso.sh" "chmod a+x"

{
  set -e
  bash $DERVICEBOOTISOSCRIPT "$BOOTISO" "$SQUASHFS" "$NEWISO"
  echo "New installation ISO: $NEWISO"
  [[ -n "$CLEAN" ]] && rm $CLEAN || :
}
