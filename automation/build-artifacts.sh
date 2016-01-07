# vim: et sts=2 sw=2

set -ex

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
export ISOURL=http://mirrors.easynews.com/linux/centos/7/os/x86_64/images/boot.iso
export TMPDIR=$PWD/tmp
export LIBGUESTFS_BACKEND=direct

prepare() {
  virt-host-validate || :

  mkdir "$TMPDIR"
  mkdir "$ARTIFACTSDIR"
}

build() {
  sudo -E make squashfs

  ln -v \
    *.squashfs.img \
    *.log \
    *-manifest-rpm \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

check() {
  sudo -E make installed-squashfs
  sudo -E make check
  ln -fv tests/*.xml \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

prepare
build
# check || :
