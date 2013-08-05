#!/bin/bash

. build.include
. toolchain.include

# @DESCRIPTION: make wrapper. It automatically appends the cross compiler
# options.
# @USAGE: xbmake [args]
xbmake() {
    bmake -C "${S}" CC="${CTARGET}-gcc" "${@}"
}

src_prepare() {
    build_src_prepare || return 1
    cross_setup_environment || return 1
    work_rootfs_setup_environment || return 1
}

src_configure() { :; }

src_compile() {
    cd "${S}" || return 1

    echo "Benchmark compile config: ${BENCHMARK_CFLAGS_CONFIG}"

    local target cflags s oldifs
    while read s; do
        if [ "${s}" = "--" ]; then
            break
        fi
        target="${s/:*}"
        cflags="${s/*:}"
        cflags="${cflags##*( )}"  # trim leading whitespaces
        echo "Compiling benchmark, target: ${target}, CFLAGS: ${cflags}"
        xbmake CFLAGS="${cflags}" EXE="benchmark.${target}" \
            || return 1
    done < "${BENCHMARK_CFLAGS_CONFIG}"
}

src_install() {
    work_rootfs_unset_environment || return 1

    mkdir "${TARGET_DIR}" || return 1

    local bench_dir="${TARGET_DIR}/benchmark"
    mkdir -p "${bench_dir}" || return 1

    local ex n
    for ex in "${S}"/benchmark.*; do
        n=$(basename "${ex}")
        echo "Installing ${ex} into ${bench_dir}"
        cp "${ex}" "${bench_dir}/${n}" || return 1
        chmod +x "${bench_dir}/${n}" || return 1
    done
    # copy the .pcm files
    cp "${S}"/*.pcm "${bench_dir}/" || return 1
    cp -rp "${S}/c100b16" "${bench_dir}/" || return 1
}

main
