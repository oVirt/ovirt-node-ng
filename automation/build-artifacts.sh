# vim: et sts=2 sw=2

set -x

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
export TMPDIR=/var/tmp/

prepare() {
  git submodule update --init --recursive
}

build() {
  make image-build ovirt-node-ng-manifest-rpm

  mkdir "$ARTIFACTSDIR"

  mv -v \
    *.qcow2 \
    *.squashfs.img \
    *.log \
    *-manifest-rpm \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

prepare_boot() {
  # The squashfs url is now pointing to the image in the jenkins instance
  local SQUASHFS_URL="$JOB_URL/lastSuccessfulBuild/artifact/exported-artifacts/ovirt-node-ng.squashfs.img"

  # Also update the kickstarts to point to that url
  sed "s#@SQUASHFS_URL@#$SQUASHFS_URL#" interactive-installation.ks.in > interactive-installation.ks
  sed "s#@SQUASHFS_URL@#$SQUASHFS_URL#" ovirt-node-ng-auto-installation.ks.in > ovirt-node-ng-auto-installation.ks
  sed -i -e "/http_proxy=/ d" -e "s/^poweroff/reboot/" *-installation.ks

  bash image-tools/bootstrap_anaconda centos 7

  mv -v \
    *.ks .treeinfo \
    "$ARTIFACTSDIR/"

  # FIXME these files should to go to images/ at some point as well
  mv -v \
    vmlinuz initrd.img squashfs.img upgrade.img \
    "$ARTIFACTSDIR/"

  mkdir -p "$ARTIFACTSDIR/images/"

  ls -shal "$ARTIFACTSDIR/" "$ARTIFACTSDIR/images" || :
}

prepare
build
prepare_boot
