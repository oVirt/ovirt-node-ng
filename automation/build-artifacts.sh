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

prepare
build
