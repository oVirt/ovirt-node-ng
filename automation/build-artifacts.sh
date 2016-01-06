# vim: et sts=2 sw=2

set -ex

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
export TMPDIR=$PWD/tmp
export LIBGUESTFS_BACKEND=direct

prepare() {
  mkdir "$TMPDIR"
  mkdir "$ARTIFACTSDIR"
}

build() {
  sudo -E make squashfs

  mv -v \
    *.squashfs.img \
    *.log \
    *-manifest-rpm \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

check() {
  sudo -E make installed-squashfs
  sudo -E make check
  mv -fv tests/*.xml \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

prepare
build
check || :
