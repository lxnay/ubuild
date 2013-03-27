#!/bin/bash

. "$(dirname "${0}")/build.include"

PN="binutils"
SRC_URI="http://ftp.gnu.org/gnu/${PN}/${UBUILD_TARBALL_NAME}"

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="/usr" \
        --with-sysroot="${UBUILD_ROOTFS_DIR}/"
}

src_install() {
    build_src_install
}

main "${PN}"
