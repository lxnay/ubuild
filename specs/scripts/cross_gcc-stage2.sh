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
        --disable-libssp \
        --disable-libmudflap \
        --disable-bootstrap \
        --disable-libgcj \
        --enable-__cxa_atexit \
        --enable-clocale=gnu \
        --enable-libstdcxx-time \
        --enable-libgomp \
        --enable-checking=release \
        --enable-languages=c,c++,fortran \
        --with-mpfr="${CROSS_TOOLS_DIR}/usr" \
        --with-gmp="${CROSS_TOOLS_DIR}/usr" \
        --with-mpc="${CROSS_TOOLS_DIR}/usr" \
        ${GCC_CONFIGURE_ARGS}
}

src_install() {
    bmake DESTDIR="${TARGET_DIR}" install || return 1
}

main
