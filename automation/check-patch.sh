# vim: et sts=2 sw=2

set -ex

# Fix to get all branch informations
git -c remote.origin.fetch=+refs/heads/*:refs/remotes/origin/* fetch

export BRANCH=${GIT_BRANCH:-$(git describe --all --contains HEAD | egrep -o "[^/]*$")}
export BRANCH=${BRANCH#*/}

export ARTIFACTSDIR=$PWD/exported-artifacts

export PATH=$PATH:/sbin:/usr/sbin
export TMPDIR=$PWD/tmp

export LIBGUESTFS_BACKEND=direct
# Short TMPDIR otherwise we run into trouble with guestfish < 1.33.27-1.fc24
# # -x -v to be more verbose
export LIBGUESTFS_TMPDIR=/var/tmp
export LIBGUESTFS_CACHEDIR=$LIBGUESTFS_TMPDIR

save_logs() {
  sudo ln -fv \
    data/ovirt-node*.ks \
    *.log \
    "$ARTIFACTSDIR/"
}

trap save_logs EXIT

prepare() {
  mknod /dev/kvm c 10 232 || :
  mkdir /dev/net || :
  mknod /dev/net/tun c 10 200 || :
  chmod 0666 /dev/net/tun || :
  mknod /dev/vhost-net c 10 238 || :
  modprobe tun vhost_net
  virt-host-validate || :
  seq 0 9 | xargs -I {} mknod /dev/loop{} b 7 {} || :

  mkdir "$TMPDIR"
  mkdir "$ARTIFACTSDIR"
  echo "Defaults !requiretty" >> /etc/sudoers

  virsh list --name | xargs -rn1 virsh destroy || true
  virsh list --all --name | xargs -rn1 virsh undefine --remove-all-storage || true
  losetup -O BACK-FILE | grep iso$ | xargs -r umount -vf
}

build() {
  # Build the squashfs for a later export
  ./autogen.sh --with-tmpdir=/var/tmp

  sudo -E make squashfs &
  sudo -E tail -f virt-install.log --pid=$! --retry ||:
  sudo -E make product.img rpm
  sudo -E make offline-installation-iso

  sudo mv -fv ovirt-node-ng-image.squashfs.img \
              ovirt-node-ng-image-$(date +%Y%m%d).squashfs.img

  sudo ln -fv \
    *manifest* \
    *unsigned* \
    tmp.repos/SRPMS/*.rpm \
    tmp.repos/RPMS/noarch/*.rpm \
    ovirt-node*.squashfs.img \
    product.img \
    ovirt-node*.iso \
    "$ARTIFACTSDIR/"
}

check() {
  # script is used, because virt-install requires a tty
  # (which ain't available in Jenkins)
  touch lock
  timeout=1200 #in secs
  sudo -E script -efqc "make installed-squashfs && make check && rm -rf lock"
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

  sudo ln -fv \
    ovirt-node-ng-image.installed.qcow2 \
    "$ARTIFACTSDIR/"
}

prepare
build
# DISABLE checks until they are fixed
#check
