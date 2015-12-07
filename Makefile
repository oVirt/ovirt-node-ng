
DISTRO=centos
RELEASEVER=7

# Builds the rootfs
image-build: ovirt-node-appliance.qcow2
	cp -v virt-install.log virt-install-$@.log

# Simulates an auto-installation
image-install: SQUASHFS_URL="@HOST_HTTP@/ovirt-node-appliance.squashfs.img"
image-install: ovirt-node-appliance-auto-installation.ks.in ovirt-node-appliance.squashfs.img
	sed -e "s#@SQUASHFS_URL@#$(SQUASHFS_URL)#" ovirt-node-appliance-auto-installation.ks.in > ovirt-node-appliance-auto-installation.ks
	$(MAKE) -f image-tools/build.mk DISTRO=$(DISTRO) RELEASEVER=$(RELEASEVER) DISK_SIZE=$$(( 10 * 1024 )) SPARSE= ovirt-node-appliance-auto-installation.qcow2
	cp -v anaconda.log anaconda-$@.log

ovirt-node-appliance-auto-installation.ks.in:
	ln -sv data/$@ .

ovirt-node-appliance.ks:
	ln -sv data/$@ .

verrel:
	@bash image-tools/image-verrel rootfs org.ovirt.Node x86_64

%.qcow2: %.ks
# Ensure that the url line contains the distro
	sudo python scripts/ovirt-node-ng-build-tool.py --qcow-debug --base $(DISTRO)$(RELEASEVER) --kickstart $< $@

%.squashfs.img: %.ks
	python scripts/ovirt-node-ng-build-tool.py --base $(DISTRO)$(RELEASEVER) --kickstart $< $@

%-manifest-rpm: %.qcow2
	 guestfish --ro -i -a $< sh 'rpm -qa | sort -u' > $@

# Direct for virt-sparsify: http://libguestfs.org/guestfs.3.html#backend
export LIBGUESTFS_BACKEND=direct
# Workaround nest problem: https://bugzilla.redhat.com/show_bug.cgi?id=1195278
export LIBGUESTFS_BACKEND_SETTINGS=force_tcg
export TEST_NODE_ROOTFS_IMG=$(PWD)/ovirt-node-appliance.qcow2
export TEST_NODE_SQUASHFS_IMG=$(PWD)/ovirt-node-appliance.squashfs.img
export PYTHONPATH=$(PWD)/../tests/
# We explicitly set now targets (i.e. qcow2 images) as dependencies
# building them is up to the user
check:
	pyflakes tests/*.py
	pep8 tests/*.py
	cd tests && nosetests --with-xunit -v -w .

clean:
	-rm -vf ovirt-node-appliance.qcow2 ovirt-node-appliance.squashfs.img ovirt-node-appliance-manifest-rpm
