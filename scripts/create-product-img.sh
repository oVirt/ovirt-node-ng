# Guides:
# https://fedoraproject.org/wiki/Anaconda/ProductImage#Product_image
# https://git.fedorahosted.org/cgit/fedora-logos.git/tree/anaconda

set -x

ISFINAL=${ISFINAL:-False}
DSTDIR=$PWD
TOPDIR=$(dirname $0)
PRDDIR=$TOPDIR/product/
PIXMAPDIR=$PRDDIR/usr/share/anaconda/pixmaps

mkdir -p "$PRDDIR" "$PIXMAPDIR"
cp -v $TOPDIR/sidebar-logo.png "$PIXMAPDIR/"

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

pushd $TOPDIR/product/
  find . | cpio -c -o | pigz -9cv > $DSTDIR/product.img
popd

unpigz < $DSTDIR/product.img | cpio -t
