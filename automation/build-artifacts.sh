#!/bin/bash -xe

export ARTIFACTSDIR=$PWD/exported-artifacts

# mock runner is not setting up the system correctly
# https://issues.redhat.com/browse/CPDEVOPS-242
dnf install -y $(cat automation/build-artifacts.req)


rm -rf "$ARTIFACTSDIR"
mkdir -p "$ARTIFACTSDIR"

./autogen.sh --disable-image --disable-docs --disable-tools

make -C src check-code
make rpm

find tmp.repos -name "*.rpm" -exec mv {} "$ARTIFACTSDIR" \;

