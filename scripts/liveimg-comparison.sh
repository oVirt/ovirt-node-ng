#!/usr/bin/bash

# Usage: $0 old-squashfs $new-squashfs

set -e

BASE=$1
MODIFIED=$2

forboth() { for TY in BASE MODIFIED; do echo "# $1 ($TY)" ; $1 ${!TY} ; done ; }

findraw() { echo $1.d/LiveOS/rootfs.img ; }

unsquash() { [[ -d $1.d ]] || unsquashfs -n -d $1.d $1 >&- ; }
forboth unsquash

BASERAW=$(findraw $BASE)
MODIFIEDRAW=$(findraw $MODIFIED)

forbothraw() { for TY in BASERAW MODIFIEDRAW; do echo "$TY ($1)" ; $1 ${!TY} ; done ; }
increase() { LC_ALL=C printf "$1:$2:$3:%0.3f\n" $(bc -l <<< "$3 / $2" ) ; }

echo "## Determining various changes from $BASE to $MODIFIED"

{
echo ":$BASE:$MODIFIED:Ratio"
size() { stat -c %s $1 ; }
BASESIZE=$(size $BASE)
MODIFIEDSIZE=$(size $MODIFIED)
increase "Size of the squashfs (deliverable)[B]" $BASESIZE $MODIFIEDSIZE

pkgcount() { guestfish -ia $1 sh "rpm -qa" | wc -l ; }
BCOUNT=$(pkgcount $BASERAW)
MCOUNT=$(pkgcount $MODIFIEDRAW)
increase "Package count" $BCOUNT $MCOUNT

diskused() { guestfish -ia $1 sh "df --output=used /" | egrep -o "[0-9]+" ; }
BDISKUSED=$(diskused $BASERAW)
MDISKUSED=$(diskused $MODIFIEDRAW)
increase "Disk usage [MB]" $BDISKUSED $MDISKUSED
} 2>&- | column -t -s :

rm -rf $BASE.d $MODIFIED.d
