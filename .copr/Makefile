.PHONY: installdeps srpm git_cfg_safe

installdeps:
	dnf -y install git autoconf automake make python3-devel

git_cfg_safe:
	# Workaround for CVE-2022-24765 fix:
	#
	#	fatal: unsafe repository ('/path' is owned by someone else)
	#
	# Since copr build process first clones the repo, and then uses mock to run the build
	#
	git config --global --add safe.directory "$(shell pwd)"

srpm: installdeps git_cfg_safe
	./autogen.sh --disable-image --disable-docs --disable-tool
	make srpm
	cp tmp.repos/SRPMS/*.src.rpm $(outdir)
