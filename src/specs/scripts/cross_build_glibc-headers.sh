#!/bin/bash

. build.include
. toolchain.include

PN="glibc-headers"
SRC_URI="http://ftp.gnu.org/gnu/${PN/-headers}/${UBUILD_TARBALL_NAME}"

src_prepare() {
    cross_sysroot_init || return 1
    cross_setup_environment || return 1
    build_src_prepare
}

src_configure() {
    export \
        libc_cv_c_cleanup=yes \
        libc_cv_forced_unwind=yes

    BUILD_CC=gcc CC="${CTARGET}-gcc" \
        CXX="${CTARGET}-g++" AR="${CTARGET}-ar" \
        AS="${CTARGET}-as" \
        RANLIB="${CTARGET}-ranlib" \
        build_src_configure \
        --prefix="/usr" \
        --with-headers="${UBUILD_BUILD_DIR}/linux-headers/usr/include" \
        --host="${CTARGET}" \
        --disable-profile \
        --without-gd --without-cvs \
        --enable-add-ons="${S}/nptl,${UBUILD_BUILD_DIR}/glibc-ports"
}

src_compile() {
    :;
}

src_install() {
    bmake install_root="${TARGET_DIR}" install-headers || return 1
    if [ -e "${S}"/bits/stdio_lim.h ]; then
        install -m 644 "${S}"/bits/stdio_lim.h \
            "${TARGET_DIR}"/usr/include/bits/ || return 1
    fi
    install -m 644 "${S}"/include/gnu/stubs.h \
        "${TARGET_DIR}"/usr/include/gnu/ || return 1

    # Make sure we install the sys-include symlink so that when
    # we build a 2nd stage cross-compiler, gcc finds the target
    # system headers correctly.  See gcc/doc/gccinstall.info
    mkdir -p "${TARGET_DIR}"/usr/"${CTARGET}" || return 1
    ln -snf usr/include "${TARGET_DIR}/usr/${CTARGET}/sys-include" || return 1

    cross_merge_target_dir_sysroot
}

main "${PN}"
