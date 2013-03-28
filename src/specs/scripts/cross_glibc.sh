#!/bin/bash

. build.include
. toolchain.include

SRC_URI="http://ftp.gnu.org/gnu/${PN}/${UBUILD_TARBALL_NAME}"

src_prepare() {
    cross_sysroot_init || return 1
    cross_setup_environment || return 1
    build_src_prepare
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

src_compile() {
    build_src_compile || bash
}

src_install() {
    bmake install_root="${TARGET_DIR}" install || return 1

    cross_merge_target_dir_sysroot
}

main
