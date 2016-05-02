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

docbookdir = $(prefix)/share/doc/@PACKAGE_NAME@/book
docbookimgsdir = $(prefix)/share/doc/@PACKAGE_NAME@/book/imgs
nodetoolsdir = $(prefix)/share/@PACKAGE_NAME@/tools

dist_doc_DATA = \
	README \
	$(NULL)

dist_docbook_DATA = \
	docs/book/administration.md \
	docs/book/book.json \
	docs/book/build.md \
	docs/book/cover.jpg \
	docs/book/customization.md \
	docs/book/design.md \
	docs/book/engine.md \
	docs/book/fsh.md \
	docs/book/getting-started.md \
	docs/book/install.md \
	docs/book/testing.md \
	docs/book/upgrade.md \
	docs/book/imgs/build-flow.dot \
	$(NULL)

dist_docbookimgs_DATA = \
	docs/book/imgs/build-flow.dot \
	docs/book/imgs/build-flow.dot.png \
	docs/book/imgs/ngn-flow-components.dot \
	docs/book/imgs/ngn-flow-components.dot.png \
	docs/book/imgs/ngn-flow.dot \
	docs/book/imgs/ngn-flow.dot.png \
	$(NULL)

dist_nodetools_DATA = \
	scripts/create-nightly-boot-iso.sh \
	scripts/derive-boot-iso.sh \
	scripts/liveimg-comparison.sh \
	scripts/ovirt-node-ng-build-tool.py \
	$(NULL)

dist_bin_SCRIPTS = \
	scripts/create-node-installation-iso \
	$(NULL)

squashfs: $(SQUASHFSFILENAME) $(RPMMANIFESTNAME)
	@echo squashfs: $(SQUASHFSFILENAME)
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
		--extra-args "inst.ks=file:///ci-image-install.ks console=ttyS0" \
		--initrd-inject data/ci-image-install.ks \
		--check disk_size=off \
		--graphics none \
		--disk path=$(INSTALLEDIMAGEFILE),size=20,bus=virtio,sparse=yes,cache=unsafe,discard=unmap,format=qcow2 \
		--disk path=$(SQUASHFSFILENAME),readonly=on,device=disk,bus=virtio,serial=livesrc
	virsh dumpxml $(DOMNAME) > installed-squashfs-domain.xml
	virsh undefine $(DOMNAME)
	@echo "The squashfs '$(SQUASHFSFILENAME)' got installed into the file '$(INSTALLEDIMAGEFILE)'"

debug-installed: installed-squashfs
	virsh define installed-squashfs-domain.xml

offline-installation-iso:
	BOOTISO=$(BOOTISO) SQUASHFS=$(SQUASHFSFILENAME) DERVICEBOOTISOSCRIPT=scripts/derive-boot-iso.sh bash scripts/create-nightly-boot-iso.sh

@BOOTISO@:
	curl $(CURLOPTS) -O @BOOTISOURL@

LMC ?= livemedia-creator
%.squashfs.img: data/%.ks @BOOTISO@
	$(LMC) --timeout 60 --make-pxe-live --iso @BOOTISO@ --ks $< --resultdir build --tmp @TMPDIR@
	mv -v build/*squash* "$@"

%.manifest-rpm: %.squashfs.img
	unsquashfs $<
	guestfish --ro -i -a 'squashfs-root/LiveOS/rootfs.img' sh 'rpm -qa | sort -u' > $@
	rm -vrf squashfs-root

RPMBUILD = rpmbuild
TMPREPOS = tmp.repos

if WITH_IMAGE
rpm srpm: $(SQUASHFSFILENAME)
else
rpm srpm:
endif
	rm -fr "$(TMPREPOS)"
	mkdir -p $(TMPREPOS)/{SPECS,RPMS,SRPMS,SOURCES}
	make dist
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
