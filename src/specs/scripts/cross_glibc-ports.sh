#!/bin/bash

. build.include
. toolchain.include

SRC_URI="http://ftp.gnu.org/gnu/${PN/-ports}/${UBUILD_TARBALL_NAME}"

src_prepare() {
    cross_sysroot_init || return 1
    build_src_prepare
}

src_configure() {
    :;
}

src_compile() {
    :;
}

src_install() {
    mkdir -p "${TARGET_DIR}" || return 1
    rsync -ax -H -A -X --delete-during "${S}"/ "${TARGET_DIR}"/ || return 1
}

main
