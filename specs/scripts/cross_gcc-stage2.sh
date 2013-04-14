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
        --prefix="/usr" \
        --with-sysroot="${CROSS_ROOT_DIR}" \
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
        --with-mpfr="${UBUILD_BUILD_DIR}/mpfr/usr" \
        --with-gmp="${UBUILD_BUILD_DIR}/gmp/usr" \
        --with-mpc="${UBUILD_BUILD_DIR}/mpc/usr" \
        ${GCC_CONFIGURE_ARGS}
}

src_install() {
    bmake DESTDIR="${TARGET_DIR}" install || return 1
}

main
