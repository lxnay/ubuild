#!/bin/bash

. build.include
. toolchain.include


PN="gcc-stage1"
TN="${UBUILD_TARBALL_NAME}"
SRC_URI="http://ftp.gnu.org/gnu/gcc/${TN%.tar*}/${TN}"

src_prepare() {
    cross_setup_environment
    build_src_prepare
}

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="/usr" \
        --with-sysroot="${SYSROOT}" \
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
    bmake DESTDIR="${TARGET_DIR}" install-gcc install-target-libgcc
}

main "${PN}"
