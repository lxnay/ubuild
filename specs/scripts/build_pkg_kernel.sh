#!/bin/bash

. build.include
. toolchain.include

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
    cross_setup_environment || return 1
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

    mkdir "${TARGET_DIR}/boot" || return 1
    cp "${BUILD_DIR}"/arch/arm/boot/uImage "${TARGET_DIR}/boot/" || return 1
    cp "${BUILD_DIR}"/System.map "${TARGET_DIR}/boot/" || return 1
    cat "${BUILD_DIR}/.config" | gzip > "${TARGET_DIR}/boot/config.gz" \
        || return 1

    cd "${BUILD_DIR}" || return 1
    xkmake -j1 modules_install || return 1
}

main
