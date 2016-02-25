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

SQUASHFSFILENAME = @IMAGENAME@.squashfs.img
RPMMANIFESTNAME = @IMAGENAME@.manifest-rpm
INSTALLEDIMAGEFILE = @IMAGENAME@.installed.qcow2

squashfs: $(SQUASHFSFILENAME) $(RPMMANIFESTNAME)
	@echo squashfs: $(SQUASHFILENAME)
	@echo squashfs rpm-manifest: $(RPMMANIFESTNAME)

installed-squashfs: DOMNAME=node-$(shell date +%F-%H%M)
installed-squashfs: data/ci-image-install.ks $(SQUASHFSFILENAME) @BOOTISO@
	virt-install \
		--name $(DOMNAME) \
		--memory 4096 \
		--vcpus 4 \
		--os-variant rhel7 \
		--rng random \
		--memballoon virtio \
		--noreboot \
		--location @BOOTISO@ \
		--extra-args "inst.ks=file:///ci-image-install.ks" \
		--initrd-inject data/ci-image-install.ks \
		--check disk_size=off \
		--disk path=$(INSTALLEDIMAGEFILE),size=20,bus=virtio,sparse=yes,cache=unsafe,discard=unmap,format=qcow2 \
		--disk path=$(SQUASHFSFILENAME),readonly=on,device=disk,bus=virtio,serial=livesrc
	virsh dumpxml $(DOMNAME) > installed-squashfs-domain.xml
	virsh undefine $(DOMNAME)
	@echo "The squashfs '$(SQUASHFSFILENAME)' got installed into the file '$(INSTALLEDIMAGEFILE)'"

debug-installed: installed-squashfs
	virsh define installed-squashfs-domain.xml

@BOOTISO@:
	curl $(CURLOPTS) -O @BOOTISOURL@

LMC ?= livemedia-creator
%.squashfs.img: data/%.ks @BOOTISO@
	$(LMC) --make-pxe-live --iso @BOOTISO@ --ks $< --resultdir build --tmp @TMPDIR@
	mv -v build/*squash* "$@"

%.manifest-rpm: %.squashfs.img
	unsquashfs $<
	guestfish --ro -i -a 'squashfs-root/LiveOS/rootfs.img' sh 'rpm -qa | sort -u' > $@
	rm -vrf squashfs-root

RPMBUILD = rpmbuild
TMPREPOS = tmp.repos
rpm srpm: $(SQUASHFSFILENAME)
	rm -fr "$(TMPREPOS)"
	mkdir -p $(TMPREPOS)/{SPECS,RPMS,SRPMS,SOURCES}
	$(RPMBUILD) --define="_topdir `pwd`/$(TMPREPOS)" --define "_sourcedir `pwd`" -ba packaging/ovirt-node-ng.spec
	@echo
	@echo "srpm and rpm(s) available at '$(TMPREPOS)'"
	@echo

clean-local:
	-rm -vrf $(SQUASHFSFILENAME) $(RPMMANIFESTNAME) $(INSTALLEDIMAGEFILE) packaging/ovirt-node-ng.spec build

check:
	$(MAKE) -C tests check

clean-build-and-check: | clean squashfs installed-squashfs check
	echo Done
