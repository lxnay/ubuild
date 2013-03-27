#!/bin/bash

. "$(dirname "${0}")/build.include"

PN="mpc"
SRC_URI="ftp://gcc.gnu.org/pub/gcc/infrastructure/${UBUILD_TARBALL_NAME}"

src_configure() {
    build_src_configure --prefix="/usr" --enable-shared \
        --with-gmp="${UBUILD_BUILD_DIR}/gmp/usr" \
        --with-mpfr="${UBUILD_BUILD_DIR}/mpfr/usr"
}

src_install() {
    build_src_install
    # delete all the .{l}a files.
    find "${TARGET_DIR}" -name "*.la" -delete
    find "${TARGET_DIR}" -name "*.a" -delete
}

main "${PN}"
