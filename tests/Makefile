
#
## A (probably incomplete) list of packages which need to be installed on the host
#

# Direct for virt-sparsify: http://libguestfs.org/guestfs.3.html#backend
export LIBGUESTFS_BACKEND=direct
# Workaround nest problem: https://bugzilla.redhat.com/show_bug.cgi?id=1195278
export LIBGUESTFS_BACKEND_SETTINGS=force_tcg

export TEST_ENGINE_ROOTFS_IMG=$(PWD)/ovirt-engine-appliance.qcow2
export TEST_NODE_ROOTFS_IMG=$(PWD)/../ovirt-node-ng.qcow2
export TEST_NODE_SQUASHFS_IMG=$(PWD)/../ovirt-node-ng.squashfs.img

export PYTHONPATH=$(PWD)

ovirt-engine-appliance.qcow2:
	echo curl -O FIXME_ADD_URL

check-code:
	@pyflakes *.py
	@pep8 *.py

check: NOSE=nosetests --with-xunit -v --no-byte-compile
check: check-code ovirt-engine-appliance.qcow2
	$(NOSE) testVirt.py testImage.py testSanity.py testIntegration.py
	-xsltproc nosetests.xslt nosetests.xml
