#!/bin/bash -xe

export ARTIFACTSDIR=$PWD/exported-artifacts

main() {
    rm -rf $ARTIFACTSDIR
    mkdir -p $ARTIFACTSDIR

    ./autogen.sh --disable-image --disable-docs --disable-tools

    make -C src check-code
    make rpm

    find tmp.repos -name "*.rpm" -exec mv {} $ARTIFACTSDIR \;
}

main
