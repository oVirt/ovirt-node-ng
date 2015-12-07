
DISTRO=centos
RELEASEVER=7

all: ovirt-node-ng.squashfs
	echo Done

# Builds the rootfs
image-build: ovirt-node-ng.qcow2
	cp -v virt-install.log virt-install-$@.log

boot.iso:
	curl -O http://mirror.centos.org/centos-7/7/os/x86_64/images/boot.iso

image-install: data/ci-image-install.ks ovirt-node-ng.squashfs.img boot.iso
	virt-install \
		--name ngn-install \
		--memory 4096 \
		--vcpus 4 --cpu host \
		--os-variant rhel7 \
		--location boot.iso \
		--extra-args "inst.ks=file:///ci-image-install.ks" \
		--initrd-inject data/ci-image-install.ks \
		--disk path=ovirt-node-ng.squashfs.img,readonly=on,device=disk,bus=virtio,serial=livesrc \
		--disk path=ovirt-node-ng-auto-installation.raw,size=20,bus=virtio,sparse=yes,cache=unsafe,discard=unmap,format=raw

ovirt-node-ng.ks:
	ln -sv data/$@ .

verrel:
	@bash image-tools/image-verrel rootfs org.ovirt.Node x86_64

%.qcow2: %.ks
	# Ensure that the url line contains the distro
	python scripts/ovirt-node-ng-build-tool.py --qcow-debug --base $(DISTRO)$(RELEASEVER) --kickstart $< $@

%.squashfs.img: %.ks
	python scripts/ovirt-node-ng-build-tool.py --base $(DISTRO)$(RELEASEVER) --kickstart $< $@

%-manifest-rpm: %.qcow2
	 guestfish --ro -i -a $< sh 'rpm -qa | sort -u' > $@

clean:
	-rm -vf ovirt-node-ng.qcow2 ovirt-node-ng.squashfs.img ovirt-node-ng-manifest-rpm

clean-build-and-check: | clean image-build check
	echo Done

check:
	$(MAKE) -C tests check
