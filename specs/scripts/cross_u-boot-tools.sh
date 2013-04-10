#!/bin/bash

. build.include
. toolchain.include

src_prepare() {
    build_src_prepare || return 1
    cross_setup_environment || return 1

    # fixup compilation, see Gentoo bug #429302
    (
        cd "${S}" || exit 1
        sed -i -e "s:-g ::" tools/Makefile || exit 1
        sed -i '/include.*config.h/d' tools/env/fw_env.[ch] || exit 1
        ln -s ../include/image.h tools/ || exit 1
    ) || return 1
}

src_configure() { :; }

src_compile() {
    cd "${BUILD_DIR}" || return 1
    ARCH= ABI= bmake -C "${S}" O="${BUILD_DIR}" \
        HOSTSTRIP=: CONFIG_ENV_OVERWRITE=y tools-all || return 1
}

src_install() {
    cd "${BUILD_DIR}" || return 1
    mkdir -p "${TARGET_DIR}/usr/bin" || return 1
    cp tools/mkimage "${TARGET_DIR}/usr/bin/mkimage" || return 1
}

main
