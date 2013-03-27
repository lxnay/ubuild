#!/bin/bash

. "$(dirname "${0}")/build.include"

SRC_URI="http://ftp.gnu.org/gnu/gmp/${UBUILD_TARBALL_NAME}"

src_configure() {
    build_src_configure --prefix="/usr" --enable-cxx
}

main "gmp"
