# vim: et sts=2 sw=2

set -x

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
export TMPDIR=$PWD/tmp
export LIBGUESTFS_BACKEND=direct

prepare() {
  git submodule update --init --recursive
  mkdir $TMPDIR
}

build() {
  sudo -E make image-build
  sudo -E make ovirt-node-ng-manifest-rpm
  sudo -E make image-install

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
