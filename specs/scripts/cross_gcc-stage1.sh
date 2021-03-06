#!/bin/bash

. build.include
. toolchain.include

src_prepare() {
    cross_setup_environment || return 1
    build_src_prepare
}

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="${CROSS_PREFIX_DIR}" \
        --with-sysroot="${CROSS_SYSROOT_DIR}" \
        --without-headers --with-newlib --disable-shared \
        --disable-threads --disable-libssp --disable-libgomp \
        --disable-libmudflap --enable-languages=c \
        --with-mpfr="${CROSS_TOOLS_DIR}/usr" \
        --with-gmp="${CROSS_TOOLS_DIR}/usr" \
        --with-mpc="${CROSS_TOOLS_DIR}/usr" \
        ${GCC_CONFIGURE_ARGS}
}

src_compile() {
    bmake all-gcc all-target-libgcc
}

src_install() {
    bmake DESTDIR="${TARGET_DIR}" install-gcc install-target-libgcc || return 1
}

main
