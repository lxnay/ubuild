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
    build_src_prepare || return 1
    cross_setup_environment || return 1

    # check if lzop and mkimage are found.
    which lzop 2>&1 > /dev/null
    if [ "${?}" != "0" ]; then
        echo "lzop not found, please install it" >&2
        return 1
    fi
}

src_configure() {
    cd "${BUILD_DIR}" || return 1

    if [ -n "${KERNEL_CONFIG}" ]; then
        cp "${KERNEL_CONFIG}" "${BUILD_DIR}/.config" || return 1
    else
        xkmake ${KERNEL_DEFCONFIG} || return 1
    fi
    xkmake oldconfig || return 1
}

src_compile() {
    cd "${BUILD_DIR}" || return 1
    xkmake zImage modules dtbs || return 1

    # if CONFIG_ARCH_MULTIPLATFORM=y (which is what we want)
    # then the generated uImage contains dummy kernel load
    # and entrypoint addresses.
    # see: https://patchwork.kernel.org/patch/1971651/
    # For this reason, uImage must be generated manually.
    mkimage -A arm -O linux -T kernel -C none \
        -a "${UBOOT_KERNEL_ADDRESS}" -e "${UBOOT_KERNEL_ENTRYPOINT}" \
        -n "ubuild.$(basename "${UBUILD_SOURCES}")" \
        -d "${BUILD_DIR}"/arch/arm/boot/zImage \
        "${BUILD_DIR}"/arch/arm/boot/uImage || return 1
}

src_install() {
    mkdir "${TARGET_DIR}" || return 1

    mkdir "${TARGET_DIR}/boot" || return 1
    cp "${BUILD_DIR}"/arch/arm/boot/uImage "${TARGET_DIR}/boot/" || return 1
    cp "${BUILD_DIR}"/System.map "${TARGET_DIR}/boot/" || return 1
    cp "${BUILD_DIR}"/arch/arm/boot/dts/*.dtb "${TARGET_DIR}/boot/" || return 1
    cat "${BUILD_DIR}/.config" | gzip > "${TARGET_DIR}/boot/config.gz" \
        || return 1

    cd "${BUILD_DIR}" || return 1
    xkmake -j1 modules_install || return 1
}

main
