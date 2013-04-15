#!/bin/bash

. build.include
. toolchain.include

src_prepare() {
    cross_setup_environment || return 1
    build_src_prepare
}

src_configure() {
    export \
        libc_cv_c_cleanup=yes \
        libc_cv_forced_unwind=yes

    BUILD_CC=gcc CC="${CTARGET}-gcc" \
        CXX="${CTARGET}-g++" AR="${CTARGET}-ar" \
        AS="${CTARGET}-as" \
        RANLIB="${CTARGET}-ranlib" \
        build_src_configure \
        --prefix="/usr" \
        --with-headers="${CROSS_SYSROOT_DIR}/usr/include" \
        --host="${CTARGET}" \
        --disable-profile \
        --without-gd --without-cvs \
        --enable-add-ons="${S}/nptl,${UBUILD_BUILD_DIR}/glibc-ports"
}

src_compile() {
    :;
}

src_install() {
    local base_sysroot="$(dirname "${CROSS_SYSROOT_PREFIX_DIR}")"

    mkdir -p "${TARGET_DIR}/${base_sysroot}" || return 1
    bmake install_root="${TARGET_DIR}/${base_sysroot}" \
        install-headers || return 1
    if [ -e "${S}"/bits/stdio_lim.h ]; then
        install -m 644 "${S}"/bits/stdio_lim.h \
            "${TARGET_DIR}${CROSS_SYSROOT_PREFIX_DIR}/include/bits/" \
            || return 1
    fi
    install -m 644 "${S}"/include/gnu/stubs.h \
        "${TARGET_DIR}${CROSS_SYSROOT_PREFIX_DIR}/include/gnu/" || return 1

    # Make sure we install the sys-include symlink so that when
    # we build a 2nd stage cross-compiler, gcc finds the target
    # system headers correctly.  See gcc/doc/gccinstall.info
    mkdir -p "${TARGET_DIR}${CROSS_SYSROOT_PREFIX_DIR}/${CTARGET}" || return 1
    ln -snf usr/include \
        "${TARGET_DIR}${CROSS_SYSROOT_PREFIX_DIR}/${CTARGET}/sys-include" \
        || return 1
}

main
