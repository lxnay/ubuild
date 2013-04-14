#!/bin/bash

. build.include

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="/usr" \
        --with-sysroot="${CROSS_ROOT_DIR}"
}

main
