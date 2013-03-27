#!/bin/bash

. build.include

PN="mpfr"
SRC_URI="http://ftp.gnu.org/gnu/${PN}/${UBUILD_TARBALL_NAME}"

src_configure() {
    build_src_configure --prefix="/usr" --enable-shared \
        --with-gmp="${UBUILD_BUILD_DIR}/gmp/usr"
}

src_install() {
    build_src_install
    # delete all the .{l}a files.
    find "${TARGET_DIR}" -name "*.la" -delete
    find "${TARGET_DIR}" -name "*.a" -delete
}

main "${PN}"
