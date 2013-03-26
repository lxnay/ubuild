#!/bin/bash

. "$(dirname "${0}")/build.include"

src_configure() {
    build_src_configure --prefix="/usr" --enable-cxx
}

main "gmp"
