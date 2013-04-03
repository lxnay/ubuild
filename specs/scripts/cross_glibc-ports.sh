#!/bin/bash

. build.include

src_configure() {
    :;
}

src_compile() {
    :;
}

src_install() {
    mkdir -p "${TARGET_DIR}" || return 1
    rsync -ax -H -A -X --delete-during "${S}"/ "${TARGET_DIR}"/ || return 1
}

main
