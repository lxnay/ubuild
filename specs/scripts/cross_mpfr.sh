#!/bin/bash

. build.include

src_configure() {
    build_src_configure --prefix="/usr" --enable-shared \
        --with-gmp="${UBUILD_BUILD_DIR}/gmp/usr"
}

src_install() {
    build_src_install || return 1
    # delete all the .{l}a files.
    find "${TARGET_DIR}" -name "*.la" -delete
    find "${TARGET_DIR}" -name "*.a" -delete
}

main
