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

build() {
  # Build the squashfs for a later export
  ./autogen.sh --with-tmpdir=/var/tmp

  # Add this jenkins job as a repository
  cat <<EOF >> data/ovirt-node-ng-image.ks

%post
yum-config-manager --add-repo "http://jenkins.ovirt.org/job/ovirt-node-ng_master_build-artifacts-fc22-x86_64/lastSuccessfulBuild/artifact/exported-artifacts/"
%end
EOF

  sudo -E make squashfs
  sudo -E make rpm

  mv -fv \
    *manifest* \
    tmp.repos/RPMS/noarch/*.rpm \
    *.squashfs.img \
    "$ARTIFACTSDIR/"
}

check() {
  sudo -E make check
  ln -fv \
    *.img \
    tests/*.xml \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

repofy() {
  pushd "$ARTIFACTSDIR/"
  createrepo .
  popd
}

prepare
build

repofy
