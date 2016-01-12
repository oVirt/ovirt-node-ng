
#
## A (probably incomplete) list of packages which need to be installed on the host
#

# Direct for virt-sparsify: http://libguestfs.org/guestfs.3.html#backend
export LIBGUESTFS_BACKEND=direct
# Workaround nest problem: https://bugzilla.redhat.com/show_bug.cgi?id=1195278
# export LIBGUESTFS_BACKEND_SETTINGS=force_tcg

TEST_DIR= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
export TEST_ENGINE_ROOTFS_IMG=$(TEST_DIR)/ovirt-engine-appliance.qcow2
export TEST_NODE_SQUASHFS_IMG=$(TEST_DIR)/../ovirt-node-ng.squashfs.img
export TEST_NODE_INSTALLED_IMG=$(TEST_DIR)/../installed-ovirt-node-ng-squashfs.raw

export PYTHONPATH=$(PWD)

ovirt-engine-appliance.qcow2:
	curl -O http://jenkins.ovirt.org/job/ovirt-appliance_master_build-artifacts-el7-x86_64/lastStableBuild/artifact/exported-artifacts/ovirt-engine-appliance.qcow2

check-code:
	@pyflakes *.py
	@pep8 *.py

check: check-code ovirt-engine-appliance.qcow2
	nosetests --with-xunit -v --no-byte-compile
	-xsltproc nosetests.xslt nosetests.xml
