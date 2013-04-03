#!/bin/bash

. build.include

src_configure() {
    build_src_configure \
        --target="${CTARGET}" \
        --prefix="/usr" \
        --with-sysroot="${CROSS_SYSROOT}"
}

main
