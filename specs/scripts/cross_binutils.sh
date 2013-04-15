#!/bin/bash

. build.include

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="${CROSS_PREFIX_DIR}" \
        --with-sysroot="${CROSS_SYSROOT_DIR}"
}

main
