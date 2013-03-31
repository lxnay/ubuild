#!/bin/bash

. build.include
. toolchain.include

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
        --without-headers --with-newlib --disable-shared \
        --disable-threads --disable-libssp --disable-libgomp \
        --disable-libmudflap --enable-languages=c \
        --with-mpfr="${UBUILD_BUILD_DIR}/mpfr/usr" \
        --with-gmp="${UBUILD_BUILD_DIR}/gmp/usr" \
        --with-mpc="${UBUILD_BUILD_DIR}/mpc/usr"
}

src_compile() {
    bmake all-gcc all-target-libgcc
}

src_install() {
    bmake DESTDIR="${TARGET_DIR}" install-gcc install-target-libgcc || return 1
    cross_merge_target_dir_sysroot
}

main
