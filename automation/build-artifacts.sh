# vim: et sts=2 sw=2

set -ex

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
export TMPDIR=$PWD/tmp
export LIBGUESTFS_BACKEND=direct

prepare() {
  git submodule update --init --recursive
  mkdir $TMPDIR
  mkdir "$ARTIFACTSDIR"
}

build() {
  sudo -E make image-build
  sudo -E make ovirt-node-ng-manifest-rpm
  sudo -E make image-install

  mv -v \
    *.qcow2 \
    *.raw \
    *.squashfs.img \
    *.log \
    *-manifest-rpm \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

check() {
  sudo -E make check
  mv -fv tests/*.xml \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

prepare
build
check || :
