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
        --with-headers="${UBUILD_BUILD_DIR}/linux-headers/usr/include" \
        --host="${CTARGET}" --enable-bind-now \
        --disable-profile --without-gd \
        --without-cvs --disable-multi-arch \
        --enable-obsolete-rpc --enable-kernel=2.6.9 \
        --enable-add-ons="nptl,libidn,${UBUILD_BUILD_DIR}/glibc-ports"
}

src_install() {
    bmake install_root="${TARGET_DIR}" install || return 1
}

main
