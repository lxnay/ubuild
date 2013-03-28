#!/bin/bash

. build.include
. toolchain.include

PN="linux-headers"
SRC_URI="http://www.kernel.org/pub/linux/kernel/v3.x/${UBUILD_TARBALL_NAME}"

src_configure() {
    :;
}

src_prepare() {
    cross_sysroot_init || return 1
    build_src_prepare
}

src_compile() {
    BUILD_DIR="${S}" \
        bmake -j1 ARCH="${ARCH}" CROSS_COMPILE="${CTARGET}-" \
        O="${BUILD_DIR}" headers_check
}

src_install() {
    BUILD_DIR="${S}" \
        bmake -j1 ARCH="${ARCH}" CROSS_COMPILE="${CTARGET}-" \
        INSTALL_HDR_PATH="${TARGET_DIR}" \
        O="${BUILD_DIR}" headers_install || return 1
    cross_merge_target_dir_sysroot
}

main "${PN}"
