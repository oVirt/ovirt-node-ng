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
  #
  # Some preparations to allow installing the image remotely from jenkins
  #

  # The squashfs url is now pointing to the image in the jenkins instance
  local SQUASHFS_URL="$JOB_URL/lastSuccessfulBuild/artifact/exported-artifacts/ovirt-node-ng.squashfs.img"

  # Also update the kickstarts to point to that url
  sed "s#@SQUASHFS_URL@#$SQUASHFS_URL#" docs/ks-examples/interactive-installation.ks.in > "$ARTIFACTSDIR"/interactive-installation.ks
  sed "s#@SQUASHFS_URL@#$SQUASHFS_URL#" data/ovirt-node-ng-auto-installation.ks.in > "$ARTIFACTSDIR"/ovirt-node-ng-auto-installation.ks
  sed -i -e "/http_proxy=/ d" -e "s/^poweroff/reboot/" "$ARTIFACTSDIR"/*-installation.ks

  pushd "$ARTIFACTSDIR"/
    # Anaconda uses the .treeinfo file to find stuff
    curl -O http://mirror.centos.org/centos-7/7/os/x86_64/.treeinfo
    # Let the squashfs point to the PWD, not in some subdir
    sed -i -e "s#=.*images/pxeboot/#= #" \
           -e "s#=.*LiveOS/#= #" \
           .treeinfo
  popd

  ls -shal "$ARTIFACTSDIR/" || :
}

prepare
build
prepare_boot
