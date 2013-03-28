#!/bin/bash

. build.include
. toolchain.include


PN="gcc-stage2"
TN="${UBUILD_TARBALL_NAME}"
SRC_URI="http://ftp.gnu.org/gnu/gcc/${TN%.tar*}/${TN}"

src_prepare() {
    cross_sysroot_init || return 1
    cross_setup_environment || return 1
    build_src_prepare
}

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="/usr" \
        --with-sysroot="${CROSS_SYSROOT}" \
        --disable-libssp --disable-libgomp \
        --disable-libmudflap --disable-libquadmath \
        --enable-languages=c \
        --with-mpfr="${UBUILD_BUILD_DIR}/mpfr/usr" \
        --with-gmp="${UBUILD_BUILD_DIR}/gmp/usr" \
        --with-mpc="${UBUILD_BUILD_DIR}/mpc/usr"
}

src_install() {
    bmake DESTDIR="${TARGET_DIR}" install || return 1
    cross_merge_target_dir_sysroot
}

main "${PN}"
