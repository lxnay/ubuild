#!/bin/bash

. build.include
. toolchain.include

SRC_URI="http://ftp.gnu.org/gnu/${PN}/${UBUILD_TARBALL_NAME}"

src_prepare() {
    cross_sysroot_init || return 1
    build_src_prepare
}

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="/usr" \
        --with-sysroot="${CROSS_SYSROOT}"
}

src_install() {
    build_src_install || return 1
    cross_merge_target_dir_sysroot
}

main
