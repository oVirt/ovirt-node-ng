# Guides:
# https://fedoraproject.org/wiki/Anaconda/ProductImage#Product_image
# https://git.fedorahosted.org/cgit/fedora-logos.git/tree/anaconda

DST=$(realpath ${1:-$PWD/product.img})
ISFINAL=${ISFINAL:-False}
SRCDIR=$(dirname $0)/../data/pixmaps
PRDDIR=product/
PIXMAPDIR=$PRDDIR/usr/share/anaconda/pixmaps/
KSDIR=$PRDDIR/usr/share/anaconda/

mkdir -p "$PRDDIR" "$PIXMAPDIR" "$KSDIR"
cp "$SRCDIR"/sidebar-logo.png "$PIXMAPDIR/"

# FIXME we could deliver the ks in the product.img
# but for simplicity we use the inst.ks approach
# Branding: product.img
# ks: kargs
#cp "$KSFILE" "$KSDIR"/interactive-defaults.ks

cat <<EOF > "$PRDDIR/.buildstamp"
[Main]
Product=oVirt Node Next
Version=master
BugURL=https://bugzilla.redhat.com
IsFinal=${ISFINAL}
UUID=$(date +%Y%m%d).x86_64
[Compose]
Lorax=21.30-1
EOF

pushd $PRDDIR
  find . | cpio -c -o --quiet | pigz -9c > $DST
popd

rm -rf $PRDDIR

#unpigz < $DST | cpio -t
