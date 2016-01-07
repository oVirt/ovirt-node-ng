
DISTRO=centos
RELEASEVER=7

IMAGEFILE=ovirt-node-ng.squashfs.img
RPMMANIFEST=ovirt-node-ng-manifest-rpm
INSTALLEDIMAGEFILE=installed-ovirt-node-ng-squashfs.raw
ISOURL?=http://mirror.centos.org/centos/7/os/x86_64/images/boot.iso
BOOTISO=$(shell basename $(ISOURL))
TMPDIR?=/var/tmp

squashfs: $(IMAGEFILE) $(RPMMANIFEST)
	@echo squashfs: $(IMAGEFILE)
	@echo squashfs rpm-manifest: $(RPMMANIFEST)

installed-squashfs: DOMNAME=node-$(shell date +%F-%H%M)
installed-squashfs: data/ci-image-install.ks $(IMAGEFILE) $(BOOTISO)
	virt-install \
		--name $(DOMNAME) \
		--memory 4096 \
		--vcpus 4 --cpu host \
		--os-variant rhel7 \
		--rng random \
		--memballoon virtio \
		--noreboot \
		--location $(BOOTISO) \
		--extra-args "inst.ks=file:///ci-image-install.ks" \
		--initrd-inject data/ci-image-install.ks \
		--check disk_size=off \
		--disk path=$(INSTALLEDIMAGEFILE),size=20,bus=virtio,sparse=yes,cache=unsafe,discard=unmap,format=raw \
		--disk path=$(IMAGEFILE),readonly=on,device=disk,bus=virtio,serial=livesrc
	virsh undefine $(DOMNAME)
	@echo "The squashfs '$(IMAGEFILE)' got installed into the file '$(INSTALLEDIMAGEFILE)'"

$(BOOTISO):
	curl -O $(ISOURL)

%.squashfs.img: data/%.ks $(BOOTISO)
	livemedia-creator --make-pxe-live --iso $(BOOTISO) --ks $< --resultdir build --tmp "$(TMPDIR)"
	mv -v build/*squash* "$@"

%-manifest-rpm: %.squashfs.img
	unsquashfs $<
	guestfish --ro -i -a 'squashfs-root/LiveOS/rootfs.img' sh 'rpm -qa | sort -u' > $@
	rm -vrf squashfs-root

clean:
	-rm -vf $(IMAGEFILE) $(RPMMANIFEST) $(INSTALLEDIMAGEFILE)

check:
	$(MAKE) -C tests check

clean-build-and-check: | clean squashfs installed-squashfs check
	echo Done
