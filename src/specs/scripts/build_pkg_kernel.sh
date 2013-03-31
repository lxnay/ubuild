#!/bin/bash

set -e

. build.include
. toolchain.include # ${CROSS_SYSROOT}

# @DESCRIPTION: bmake wrapper for the Linux kernel build system calls. It
# automatically appends the cross compiler options.
# @USAGE: xkmake [ærgs]
xkmake() {
    bmake -C "${S}" ARCH="${ARCH}" CROSS_COMPILE="${CTARGET}-" \
        O="${BUILD_DIR}" INSTALL_MOD_PATH="${TARGET_DIR}" \
        DESTDIR="${TARGET_DIR}" "${@}"
}

src_prepare() {
    # check if lzop and mkimage are found.
    which lzop 2>&1 > /dev/null
    if [ "${?}" != "0" ]; then
        echo "lzop not found, please install it" >&2
    fi
    which mkimage 2>&1 > /dev/null
    if [ "${?}" != "0" ]; then
        echo "mkimage not found, please install it" >&2
    fi

    build_src_prepare || return 1
    cross_setup_environment
}

src_configure() {
    cd "${BUILD_DIR}" || return 1

    if [ -n "${KERNEL_CONFIG}" ]; then
        cp "${UBUILD_PWD}/${KERNEL_CONFIG}" "${BUILD_DIR}/.config" || return 1
    else
        xkmake ${KERNEL_DEFCONFIG} || return 1
    fi
    xkmake oldconfig || return 1
}

src_compile() {
    cd "${BUILD_DIR}" || return 1
    xkmake uImage modules || return 1
}

src_install() {
    mkdir "${TARGET_DIR}" || return 1
    cd "${BUILD_DIR}" || return 1
    xkmake -j1 modules_install || return 1
}

main
