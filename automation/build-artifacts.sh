# vim: et sts=2 sw=2

set -ex

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
export CURLOPTS="-x http://proxy.phx.ovirt.org:3128"
export TMPDIR=$PWD/tmp
export LIBGUESTFS_BACKEND=direct

export BRANCH=ovirt-3.6

prepare() {
  virt-host-validate || :

  mkdir "$TMPDIR"
  mkdir "$ARTIFACTSDIR"
  echo "Defaults !requiretty" >> /etc/sudoers
}

build() {
  # Build the squashfs for a later export
  ./autogen.sh --with-tmpdir=/var/tmp

  # Add this jenkins job as a repository
  cat <<EOF >> data/ovirt-node-ng-image.ks

%post
cat > /etc/yum.repos.d/ovirt-node.repo <<__EOR__
[ovirt-node-ng-${BRANCH}]
name=oVirt Node Next (${BRANCH} Nightly)
baseurl=http://jenkins.ovirt.org/job/ovirt-node-ng_${BRANCH}_build-artifacts-fc22-x86_64/lastSuccessfulBuild/artifact/exported-artifacts/
enabled=1
gpgcheck=0
metadata_expire=60
skip_if_unavailable=1
keepcache=0
__EOR__
%end
EOF

  sudo -E make squashfs
  sudo -E make product.img rpm
  sudo -E make offline-installation-iso

  mv -fv \
    *manifest* \
    tmp.repos/RPMS/noarch/*.rpm \
    ovirt-node*.squashfs.img \
    product.img \
    ovirt-node*.iso \
    data/ovirt-node*.ks \
    *.log \
    "$ARTIFACTSDIR/"
}

check() {

  # script is used, because virt-install requires a tty
  # (which ain't available in Jenkins)
  touch lock
  timeout=1200 #in secs
  sudo -E script -efqc "make check && rm -rf lock"
  set +x
  while [ -f lock ]; do
    if [ $timeout -eq 0 ];
    then
      echo "test timeout error"
      exit 1
    fi
    timeout=$(( timeout - 1 ))
    sleep 1
  done
  set -x

  ln -fv \
    *.img \
    tests/*.xml \
    "$ARTIFACTSDIR/"

  ls -shal "$ARTIFACTSDIR/" || :
}

repofy_and_checksum() {
  pushd "$ARTIFACTSDIR/"
  createrepo .
  sha256sum * > CHECKSUMS.sha256 || :

  # Helper to redirect to latest installation iso
  INSTALLATIONISO=$(ls *.iso)
  echo "<html><head><meta http-equiv='refresh' content='0; url=$INSTALLATIONISO' /></head></html>" > latest-installation-iso.html
  popd
}
prepare
build

repofy_and_checksum
