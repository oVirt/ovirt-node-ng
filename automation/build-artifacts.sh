# vim: et sts=2 sw=2

set -ex

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
export CURLOPTS="-x http://proxy.phx.ovirt.org:3128"
export TMPDIR=$PWD/tmp
export LIBGUESTFS_BACKEND=direct

prepare() {
  virt-host-validate || :

  mkdir "$TMPDIR"
  mkdir "$ARTIFACTSDIR"
}

check() {
  sudo -E make installed-squashfs
  sudo -E make check
  ln -fv \
    *.img \
    tests/*.xml \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

prepare
check || :
