srpm:
	dnf -y install git autoconf automake make asciidoc
	./autogen.sh --disable-image --disable-docs --disable-tool
	make srpm
	cp tmp.repos/SRPMS/*.src.rpm $(outdir)
