#!/bin/bash

. build.include

PN="binutils"
SRC_URI="http://ftp.gnu.org/gnu/${PN}/${UBUILD_TARBALL_NAME}"

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="/usr" \
        --with-sysroot="${SYSROOT}"
}

src_install() {
    build_src_install
}

main "${PN}"
