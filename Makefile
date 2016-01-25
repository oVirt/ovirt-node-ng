# Copyright (C) 2016 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.
DISTRO=centos
RELEASEVER=7

IMAGEFILE=rootfs\:org.ovirt.Node.Next\:x86_64\:0.squashfs.img
RPMMANIFEST=rootfs\:org.ovirt.Node.Next\:x86_64\:0-manifest-rpm
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
	curl $(CURLOPTS) -O $(ISOURL)

%.squashfs.img: data/%.ks $(BOOTISO)
	livemedia-creator --make-pxe-live --iso $(BOOTISO) --ks $< --resultdir build --tmp "$(TMPDIR)"
	mv -v build/*squash* "$@"

%-manifest-rpm: %.squashfs.img
	unsquashfs $<
	guestfish --ro -i -a 'squashfs-root/LiveOS/rootfs.img' sh 'rpm -qa | sort -u' > $@
	rm -vrf squashfs-root

clean:
	-rm -vf $(IMAGEFILE) $(RPMMANIFEST) $(INSTALLEDIMAGEFILE)

check: installed-squashfs
	$(MAKE) -C tests check

clean-build-and-check: | clean squashfs installed-squashfs check
	echo Done

ovirt-node-ng.spec: VERSION=1.0
ovirt-node-ng.spec: VERSION_EXTRA=
ovirt-node-ng.spec: RELEASE=$(shell date +%Y%m%d).1
ovirt-node-ng.spec: PLACEHOLDER=002-0.6
ovirt-node-ng.spec: SQUASHFILENAME=$(IMAGEFILE)
ovirt-node-ng.spec: data/ovirt-node-ng.spec.in
	sed \
	-e "s/@VERSION@/$(VERSION)$(VERSION_EXTRA)/" \
	-e "s/@RELEASE@/$(RELEASE)/" \
	-e "s/@SQUASHFILENAME@/$(SQUASHFILENAME)/" \
	-e "s/@PLACEHOLDER@/$(PLACEHOLDER)/" \
	$< > $@

%.rpm: %.spec
	rpmbuild --define "_sourcedir `pwd`" -ba $<

RPMBUILD = rpmbuild
TMPREPOS = tmp.repos
rpm srpm: ovirt-node-ng.spec $(IMAGEFILE)
	rm -fr "$(TMPREPOS)"
	mkdir -p $(TMPREPOS)/{SPECS,RPMS,SRPMS,SOURCES}
	$(RPMBUILD) --define="_topdir `pwd`/$(TMPREPOS)" --define "_sourcedir `pwd`" -ba $<
	@echo
	@echo "srpm and rpm(s) available at '$(TMPREPOS)'"
	@echo
