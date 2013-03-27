#!/bin/bash

. build.include

PN="glibc-ports"
SRC_URI="http://ftp.gnu.org/gnu/${PN/-ports}/${UBUILD_TARBALL_NAME}"

src_configure() {
    :;
}

src_compile() {
    :;
}

src_install() {
    mkdir -p "${TARGET_DIR}"
    rsync -ax -H -A -X --delete-during "${S}"/ "${TARGET_DIR}"/
}

main "${PN}"
