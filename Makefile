
DISTRO=centos
RELEASEVER=7

ifdef TMPDIR
BUILD_ARGS = --tmp-dir $(TMPDIR)
endif

ifdef LIBGUESTFS_BACKEND
GUESTFISH_ARGS = LIBGUESTFS_BACKEND=$(LIBGUESTFS_BACKEND)
endif

all: ovirt-node-ng.squashfs
	echo Done

# Builds the rootfs
image-build: ovirt-node-ng.qcow2
	cp -v virt-install.log virt-install-$@.log

boot.iso:
	curl -O http://mirror.centos.org/centos-7/7/os/x86_64/images/boot.iso

image-install: data/ci-image-install.ks ovirt-node-ng.squashfs.img boot.iso
	#curl "http://mirror.centos.org/centos/7/os/x86_64/Packages/" | grep centos-release-7-2 || ( echo "ERROR: CentOS 7.2 is required" ; exit 1  ; )
	virt-install \
		--name $@-$(shell date +%F-%H%M) \
		--memory 4096 \
		--vcpus 4 --cpu host \
		--os-variant rhel7 \
		--rng random \
		--noreboot \
		--location boot.iso \
		--extra-args "inst.ks=file:///ci-image-install.ks" \
		--initrd-inject data/ci-image-install.ks \
		--disk path=ovirt-node-ng-auto-installation.raw,size=20,bus=virtio,sparse=yes,cache=unsafe,discard=unmap,format=raw \
		--disk path=ovirt-node-ng.squashfs.img,readonly=on,device=disk,bus=virtio,serial=livesrc

verrel:
	@bash image-tools/image-verrel rootfs org.ovirt.Node x86_64

%.qcow2: data/%.ks boot.iso
	# Ensure that the url line contains the distro
	python scripts/ovirt-node-ng-build-tool.py $(BUILD_ARGS) --qcow-debug --base boot.iso --kickstart $< $@

%.squashfs.img: data/%.ks boot.iso
	python scripts/ovirt-node-ng-build-tool.py $(BUILD_ARGS) --base boot.iso --kickstart $< $@

%-manifest-rpm: %.qcow2
	 $(GUESTFISH_ARGS) guestfish --ro -i -a $< sh 'rpm -qa | sort -u' > $@

clean:
	-rm -vf ovirt-node-ng.qcow2 ovirt-node-ng.squashfs.img ovirt-node-ng-manifest-rpm

clean-build-and-check: | clean image-build check
	echo Done

check:
	$(MAKE) -C tests check
