
# Direct for virt-sparsify: http://libguestfs.org/guestfs.3.html#backend
export LIBGUESTFS_BACKEND=direct

TEST_DIR= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
export TEST_ENGINE_ROOTFS_IMG=$(TEST_DIR)/ovirt-engine-appliance.qcow2
export TEST_NODE_INSTALLED_IMG=$(TEST_DIR)/../ovirt-node-ng-image.installed.qcow2

export PYTHONPATH=$(PWD)

check-code:
	pyflakes $(wildcard *.py)
	pep8 $(wildcard *.py)

pre-check:
	@( [[ ! -e /sys/fs/selinux/enforce ]] || grep -q 0 /sys/fs/selinux/enforce ) || ( echo ERROR: Enable permissive mode: seteneforce 0 ; exit 1 )
#	@firewall-cmd -q --query-port 1234/udp || ( echo ERROR: Open port 1234/udp for multicaset for testing: firewall-cmd --add-port 1234/udp ; exit 1 )

PYTEST=nosetests --with-xunit -v --no-byte-compile --stop
check: pre-check check-code check-sanity
	@echo PASSED

check-sanity: check-code
	$(PYTEST) testVirt.py testSanity.py
	-xsltproc nosetests.xslt nosetests.xml

check-integration: #check-sanity ovirt-engine-appliance.qcow2
	@echo FIXME This is WIP and probably not working
	$(PYTEST) testIntegration.py
	-xsltproc nosetests.xslt nosetests.xml

ovirt-engine-appliance.qcow2:
	curl -O http://jenkins.ovirt.org/job/ovirt-appliance_master_build-artifacts-el7-x86_64/lastStableBuild/artifact/exported-artifacts/ovirt-engine-appliance.qcow2
