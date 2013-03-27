#!/bin/bash

. build.include
. toolchain.include


PN="glibc"
SRC_URI="http://ftp.gnu.org/gnu/${PN}/${UBUILD_TARBALL_NAME}"

src_prepare() {
    cross_setup_environment
    build_src_prepare
}

src_configure() {
    BUILD_CC=gcc CC="${CTARGET}-gcc" \
        CXX="${CTARGET}-g++" AR="${CTARGET}-ar" \
        AS="${CTARGET}-as" \
        RANLIB="${CTARGET}-ranlib" \
        build_src_configure \
        --prefix="/usr" \
        --with-headers="${UBUILD_BUILD_DIR}/linux-headers/include" \
        --host="${CTARGET}" \
        --disable-profile \
        --without-gd --without-cvs \
        --enable-add-ons="${S}/nptl,${UBUILD_BUILD_DIR}/glibc-ports"
}

src_compile() {
    :;
}

src_install() {
    bmake install_root="${TARGET_DIR}/glibc-headers" install-headers
}

main "${PN}"
