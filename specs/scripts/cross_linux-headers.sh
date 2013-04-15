#!/bin/bash

. build.include
. toolchain.include

src_prepare() {
    cross_setup_environment || return 1
    build_src_prepare
}

src_configure() {
    :;
}

src_compile() {
    BUILD_DIR="${S}" \
        bmake -j1 ARCH="${ARCH}" CROSS_COMPILE="${CTARGET}-" \
        O="${BUILD_DIR}" headers_check
}

src_install() {
    BUILD_DIR="${S}" \
        bmake -j1 ARCH="${ARCH}" CROSS_COMPILE="${CTARGET}-" \
        INSTALL_HDR_PATH="${TARGET_DIR}/${CROSS_SYSROOT_PREFIX_DIR}" \
        O="${BUILD_DIR}" headers_install || return 1
}

main
