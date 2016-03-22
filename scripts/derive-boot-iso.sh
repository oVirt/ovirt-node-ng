#!/bin/bash

# Usage: bash derive-boot-iso.sh boot.iso ovirt-node-ng-image.squashfs.img

set -e

BOOTISO=$(realpath $1)
SQUASHFS=$(realpath $2)
NEWBOOTISO=${3:-$(dirname $BOOTISO)/new-$(basename $BOOTISO)}

TMPDIR=$(realpath bootiso.d)

die() { echo "ERROR: $@" >&2 ; exit 2 ; }
cond_out() { "$@" > .tmp.log 2>&1 || { cat .tmp.log >&2 ; die "Failed to run $@" ; } && rm .tmp.log || : ; return $? ; }

extract_iso() {
  echo "[1/4] Extracting ISO"
  cond_out checkisomd5 --verbose $BOOTISO
  local ISOFILES=$(isoinfo -i $BOOTISO -RJ -f | sort -r | egrep "/.*/")
  for F in $ISOFILES
  do
    mkdir -p ./$(dirname $F)
    [[ -d .$F ]] || { isoinfo -i $BOOTISO -RJ -x $F > .$F ; }
  done
}

add_payload() {
  echo "[2/4] Adding squashfs to ISO"
  cond_out unsquashfs -ll $SQUASHFS
  local DST=$(basename $SQUASHFS)
  cp $SQUASHFS $DST
  cat > liveimg.ks <<EOK
liveimg --url=file:///run/install/repo/$DST
autopart --type=thinp
%post --erroronfail
imgbase layout --init ovirt-node-ng-1.0-0.0
imgbase --experimental volume --create /var 4G
%end
EOK
}

modify_bootloader() {
  echo "[3/4] Updating bootloader"
  # grep -rn stage2 *
  local CFGS="EFI/BOOT/grub.cfg isolinux/isolinux.cfg"
  local PRODURL="http://jenkins.ovirt.org/job/fabiand_boo_build_testing/lastSuccessfulBuild/artifact/product.img"
  sed -i "/stage2/ s%$% inst.ks=cdrom:/liveimg.ks%" $CFGS
  sed -i "/stage2/ s%$% inst.updates=$PRODURL%" $CFGS
}

create_iso() {
  echo "[4/4] Creating new ISO"
  local volid=$(isoinfo -d -i $BOOTISO | grep "Volume id" | cut -d ":" -f2 | sed "s/^ //")
  cond_out mkisofs -J -T -o $NEWBOOTISO -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -graft-points -V "$volid" $TMPDIR
  cond_out implantisomd5 --force $NEWBOOTISO
}

main() {
  mkdir $TMPDIR
  cd $TMPDIR

  extract_iso
  add_payload
  modify_bootloader
  create_iso

  rm -rf $TMPDIR || :
}

main
