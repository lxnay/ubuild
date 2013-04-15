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

    # depends on cross compiler targets:
    # - linux-headers
    # - glibc-ports
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
    bmake install_root="${TARGET_DIR}" install || return 1

    # add ld-linux.so.3 if it doesn't exist. This is a workaround
    # for broken/old binaries.
    # NOTE: this seems to be a problem with <glibc-2.17 and
    # newer GCCs (>=4.7). Looking at the glibc-2.17 changelog,
    # this seems to be addressed there (in a non-trivial way).
    local armhf_ld="${TARGET_DIR}/lib/ld-linux-armhf.so.3"
    local sys_ld="${TARGET_DIR}/lib/ld-linux.so.3"
    if [ -e "${armhf_ld}" ] && [ ! -e "${sys_ld}" ]; then
        ln -s $(basename "${armhf_ld}") "${sys_ld}" || return 1
    fi
}

main
