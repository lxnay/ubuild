#!/bin/bash

. build.include
. toolchain.include

src_prepare() {
    build_src_prepare || return 1
    cross_setup_environment || return 1
}

src_configure() {
    export \
        libc_cv_c_cleanup=yes \
        libc_cv_forced_unwind=yes

    build_src_configure \
        --prefix="/usr" \
        --with-headers="${CROSS_SYSROOT_DIR}/usr/include" \
        --host="${CTARGET}" --enable-bind-now \
        --disable-profile --without-gd \
        --without-cvs --disable-multi-arch \
        --enable-obsolete-rpc --enable-kernel=2.6.9 \
        --enable-add-ons="nptl,libidn,${UBUILD_BUILD_DIR}/glibc-ports"
}

src_install() {
    local base_sysroot="$(dirname "${CROSS_SYSROOT_PREFIX_DIR}")"

    mkdir -p "${TARGET_DIR}/${base_sysroot}" || return 1
    bmake install_root="${TARGET_DIR}/${base_sysroot}" install || return 1
}

main
