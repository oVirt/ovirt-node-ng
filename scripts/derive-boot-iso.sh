#!/bin/bash

# Usage: bash derive-boot-iso.sh boot.iso ovirt-node-ng-image.squashfs.img

set -e

BOOTISO=$(realpath $1)
SQUASHFS=$(realpath $2)
NEWBOOTISO=$(realpath ${3:-$(dirname $BOOTISO)/new-$(basename $BOOTISO)})
PRODUCTIMG=$(realpath ./product.img)

TMPDIR=$(realpath bootiso.d)

die() { echo "ERROR: $@" >&2 ; exit 2 ; }
cond_out() { "$@" > .tmp.log 2>&1 || { cat .tmp.log >&2 ; die "Failed to run $@" ; } && rm .tmp.log || : ; return $? ; }
in_squashfs() { export TMPDIR=/var/tmp ; guestfish --ro -a ${SQUASHFS} run : mount /dev/sda / : mount-loop /LiveOS/rootfs.img / : sh "$1" ; }

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
  echo "[2/4] Adding image to ISO"
  cond_out unsquashfs -ll $SQUASHFS
  local DST=$(basename $SQUASHFS)
  # Add squashfs
  cp $SQUASHFS $DST
  cat > interactive-defaults.ks <<EOK
liveimg --url=file:///run/install/repo/$DST

# FIXME This should be fixed more elegantly with
# https://bugzilla.redhat.com/663099#c14
autopart --type=thinp

%post --erroronfail
imgbase layout --init
%end
EOK
  # Add branding
  local IMGMNT=$(mktemp -d)
  local SQMNT=$(mktemp -d)
  mount $DST $IMGMNT
  mount $IMGMNT/LiveOS/rootfs.img $IMGMNT
  unsquashfs LiveOS/squashfs.img
  mount squashfs-root/LiveOS/rootfs.img $SQMNT
  cp -f $IMGMNT/etc/os-release $SQMNT/etc
  umount $IMGMNT $IMGMNT $SQMNT
  rmdir $SQMNT $IMGMNT
  mksquashfs squashfs-root LiveOS/squashfs.img -noappend -comp xz
  rm -rf squashfs-root
  # and the kickstart
  if [[ -e "$PRODUCTIMG" ]]; then
    cp "$PRODUCTIMG" images/product.img
  fi
}

modify_bootloader() {
  echo "[3/4] Updating bootloader"
  # grep -rn stage2 *
  local EFIMNT=$(mktemp -d)
  mount -o rw images/efiboot.img $EFIMNT
  local CFGS="EFI/BOOT/grub.cfg isolinux/isolinux.cfg isolinux/grub.conf $EFIMNT/EFI/BOOT/grub.cfg"
  local LABEL=$(egrep -h -o "hd:LABEL[^ :]*" $CFGS  | sort -u)
  local ORIG_NAME=$(grep -Po "(?<=^menu title ).*" isolinux/isolinux.cfg)
  local INNER_PRETTY_NAME=$(in_squashfs "grep PRETTY_NAME /etc/os-release" | cut -d "=" -f2 | tr -d \")
  sed -i \
	-e "/stage2/ s%$% inst.ks=${LABEL//\\/\\\\}:/interactive-defaults.ks%" \
	-e "/^\s*\(append\|initrd\|linux\|search\)/! s%${ORIG_NAME}%${INNER_PRETTY_NAME}%g" \
	-e "s/Rescue a .* system/Rescue a ${INNER_PRETTY_NAME} system/g" \
	$CFGS
  umount $EFIMNT
  rmdir $EFIMNT
}

create_iso() {
  echo "[4/4] Creating new ISO"
  local volid=$(isoinfo -d -i $BOOTISO | grep "Volume id" | cut -d ":" -f2 | sed "s/^ //")
  cond_out mkisofs -J -T -U \
      -joliet-long \
      -o $NEWBOOTISO \
      -b isolinux/isolinux.bin \
      -c isolinux/boot.cat \
      -no-emul-boot \
      -boot-load-size 4 \
      -boot-info-table \
      -eltorito-alt-boot \
      -e images/efiboot.img \
      -no-emul-boot \
      -R \
      -graft-points \
      -A "$volid" \
      -V "$volid" \
      $TMPDIR
  cond_out isohybrid -u $NEWBOOTISO
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
