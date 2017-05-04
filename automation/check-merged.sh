# vim: et sts=2 sw=2

set -ex

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
# Disabled for now because we see outdated packages
#export CURLOPTS="-x http://proxy.phx.ovirt.org:3128"
export TMPDIR=$PWD/tmp
export LIBGUESTFS_BACKEND=direct

prepare() {
  virt-host-validate || :

  mkdir "$TMPDIR"
  mkdir "$ARTIFACTSDIR"
}

build() {
  ./autogen.sh --with-tmpdir=/var/tmp

  sudo -E make squashfs

  ln -v \
    *.squashfs.img \
    *.log \
    *manifest* \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

prepare
build
