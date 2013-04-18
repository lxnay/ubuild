#!/bin/bash

. build.include

src_configure() {
    :;
}

src_compile() {
    :;
}

src_install() {
    local ports_dir="${TARGET_DIR}${CROSS_PREFIX_DIR}/src/glibc-ports"
    mkdir -p "${ports_dir}" || return 1
    rsync -ax -H -A -X --delete-during "${S}"/ "${ports_dir}"/ || return 1
}

main
