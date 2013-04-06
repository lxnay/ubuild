#!/bin/bash

. build.include
. toolchain.include

# @DESCRIPTION: bmake wrapper for the Linux kernel build system calls. It
# automatically appends the cross compiler options.
# @USAGE: xkmake [ærgs]
xbbmake() {
    bmake -C "${S}" ARCH="${ARCH}" CROSS_COMPILE="${CTARGET}-" \
        O="${BUILD_DIR}" DESTDIR="${TARGET_DIR}" "${@}"
}

src_prepare() {
    build_src_prepare || return 1
    cross_setup_environment || return 1
}

src_configure() {
    cd "${BUILD_DIR}" || return 1

    if [ -n "${BUSYBOX_CONFIG}" ]; then
        cp "${BUSYBOX_CONFIG}" "${BUILD_DIR}/.config" || return 1
    else
        xkmake ${KERNEL_DEFCONFIG} || return 1
    fi
    xbbmake oldconfig || return 1
}

src_compile() {
    cd "${BUILD_DIR}" || return 1
    xbbmake || return 1
}

src_install() {
    mkdir "${TARGET_DIR}" || return 1
    xbbmake install || return 1
    rsync -ax -H -A -X "${BUILD_DIR}/_install/" "${TARGET_DIR}/" || return 1
}

main
