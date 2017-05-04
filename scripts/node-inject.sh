#!/bin/bash

[[ $# -lt 3 ]] && {
    echo "Usage: $0 <SRPM> <DST> [FILES...]"
    echo "Copies files to a squashfs packed inside a source rpm, and rebuilds "
    echo "the rpm.  If the files are rpms, they will be installed inside the "
    echo "squashfs."
    exit 1
}

[[ $EUID -ne 0 ]] && {
    echo "Must run as root"
    exit 1
}

set -e

srpm=$1
dst=$2
shift 2
files=$@

echo "SRPM=$srpm"
echo "DST=$dst"
echo "FILES=$files"

workdir=$(mktemp -d)

# extract source rpm and squashfs
squashfs=$(rpm2cpio $srpm | cpio -divuD $workdir 2>&1 | grep .squashfs)
unsquashfs -d $workdir/squashfs-root $workdir/$squashfs

# mount rootfs
mntdir=$(mktemp -d)
mount $workdir/squashfs-root/LiveOS/rootfs.img $mntdir

# make the changes on the mounted rootfs
[[ ! -d $mntdir/$dst ]] && mkdir -p $mntdir/$dst
cp $files $mntdir/$dst
rpms=""
for f in $mntdir/$dst/*
do
    [[ $f == *.rpm ]] && rpms="$rpms $f"
done
[[ -n $rpms ]] && rpm -Uhv --noscripts --root=$mntdir $rpms
umount $mntdir
rmdir $mntdir

# rebuild the squashfs and the rpm
mksquashfs $workdir/squashfs-root $workdir/$squashfs -noappend -comp xz
rpmbuild --define "_topdir $workdir" --define "_sourcedir $workdir" -bb $workdir/*.spec

# copy
mv -v $workdir/RPMS/*/*.rpm .
rm -rf $workdir
