#!/bin/bash

. build.include

PN="linux-headers"
SRC_URI="http://www.kernel.org/pub/linux/kernel/v3.x/${UBUILD_TARBALL_NAME}"

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
        INSTALL_HDR_PATH="${TARGET_DIR}" \
        O="${BUILD_DIR}" headers_install
}

main "${PN}"
