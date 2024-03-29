# Copyright (C) 2016-2022 Red Hat, Inc.
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
RPMUNSIGNEDNAME = @IMAGENAME@.unsigned-rpms
INSTALLEDIMAGEFILE = @IMAGENAME@.installed.qcow2

nodetoolsdir = $(prefix)/share/@PACKAGE_NAME@/tools

EXTRA_DIST = \
	docs/man/nodectl.8 \
	scripts/nodectl-motd.sh \
	scripts/nodectl-run-banner.sh \
	$(NULL)

SUBDIRS = \
	src \
	$(NULL)

man_MANS = \
	docs/man/nodectl.8 \
	$(NULL)

dist_doc_DATA = \
	README.md \
	$(NULL)

dist_nodetools_DATA = \
	scripts/create-nightly-boot-iso.sh \
	scripts/derive-boot-iso.sh \
	scripts/liveimg-comparison.sh \
	scripts/node-inject.sh \
	$(NULL)

dist_bin_SCRIPTS = \
	scripts/create-node-installation-iso \
	$(NULL)

dist_sbin_SCRIPTS = \
	scripts/nodectl \
	$(NULL)


# Building a "LiveOS" vm for debugging ks issues
debug-squashfs: LMCOPTS=--vnc vnc=127.0.0.1:5
debug-squashfs: | debug-ks $(SQUASHFSFILENAME)
	@echo debug-squashfs $(SQUASHFSFILENAME)

squashfs: $(SQUASHFSFILENAME) $(RPMMANIFESTNAME) $(RPMUNSIGNEDNAME)
	@echo squashfs: $(SQUASHFSFILENAME)
	@echo squashfs rpm-manifest: $(RPMMANIFESTNAME)
	@echo squashfs rpm-unsigned: $(RPMUNSIGNEDNAME)

debug-installed: installed-squashfs
	virsh define installed-squashfs-domain.xml

product.img:
	bash scripts/create-product-img.sh $@

offline-installation-iso: product.img
	PRODUCTIMG=$(PWD)/product.img \
			   BOOTISO=$(BOOTISO) \
			   SQUASHFS=$(SQUASHFSFILENAME) \
			   VERSION=$(PACKAGE_VERSION) \
			   DERVICEBOOTISOSCRIPT=scripts/derive-boot-iso.sh \
			   bash scripts/create-nightly-boot-iso.sh

@BOOTISO@:
	curl $(CURLOPTS) -LO $(BOOTISOURL)


# Short TMPDIR otherwise we run into trouble with guestfish < 1.33.27-1.fc24
# # -x -v to be more verbose
IN_ROOTFS=export LIBGUESTFS_TMPDIR=/var/tmp ; guestfish --ro -a $(SQUASHFSFILENAME) run : mount /dev/sda / : mount-loop /LiveOS/rootfs.img / : sh
$(RPMMANIFESTNAME): $(SQUASHFSFILENAME)
	$(IN_ROOTFS) "rpm -qa|sort" > $@

$(RPMUNSIGNEDNAME): $(SQUASHFSFILENAME)
	$(IN_ROOTFS) "rpm -qa --qf '%{name}-%{version}-%{release}.%{arch} (%{SIGPGP:pgpsig})\n'" | grep -v "Key ID" > $@

packaging/ovirt-node-ng.spec: PLACEHOLDER_RPM=ovirt-node-ng-image-update-placeholder
packaging/ovirt-node-ng.spec: PLACEHOLDER_RPM_VERSION=$(shell $(IN_ROOTFS) "rpm -q --qf %{version} $(PLACEHOLDER_RPM)")
packaging/ovirt-node-ng.spec: PLACEHOLDER_RPM_RELEASE=$(shell $(IN_ROOTFS) "rpm -q --qf %{release} $(PLACEHOLDER_RPM)")
packaging/ovirt-node-ng.spec: packaging/ovirt-node-ng.spec.in
	sed \
		-e "s/\@PACKAGE_VERSION\@/$(PACKAGE_VERSION)/" \
		-e "s/\@PACKAGE_RPM_VERSION\@/$(PACKAGE_RPM_VERSION)/" \
		-e "s/\@PACKAGE_RPM_RELEASE\@/$(PACKAGE_RPM_RELEASE)/" \
		-e "s/\@PLACEHOLDER_RPM_VERSION\@/$(PLACEHOLDER_RPM_VERSION)/" \
		-e "s/\@PLACEHOLDER_RPM_RELEASE\@/$(PLACEHOLDER_RPM_RELEASE)/" \
		-e "s/\@DOCS\@/$(DOCS)/" \
		-e "s/\@TOOLS\@/$(TOOLS)/" \
		$< > $@

RPMBUILD = rpmbuild
TMPREPOS = tmp.repos

rpm srpm: packaging/ovirt-node-ng.spec
	rm -fr "$(TMPREPOS)"
	mkdir -p $(TMPREPOS)/{SPECS,RPMS,SRPMS,SOURCES}
	make dist
	$(RPMBUILD) \
		--define="_topdir `pwd`/$(TMPREPOS)" \
		--define "_sourcedir `pwd`" \
		-ba packaging/ovirt-node-ng.spec
	@echo
	@echo "srpm and rpm(s) available at '$(TMPREPOS)'"
	@echo

clean-local:
	-rm -vrf $(SQUASHFSFILENAME) $(RPMMANIFESTNAME) $(RPMUNSIGNEDNAME) $(INSTALLEDIMAGEFILE) packaging/ovirt-node-ng.spec build

clean-build-and-check: | clean squashfs installed-squashfs check
	echo Done
