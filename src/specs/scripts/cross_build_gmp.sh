#!/bin/bash

set -e

if [ ${#} -lt 1 ]; then
    echo "${0} <tarball>" >&2
    exit 1
fi
WORKDIR=$(TMPDIR="${UBUILD_BUILD_DIR}" mktemp -d)
if [ ! -d "${WORKDIR}" ]; then
    echo "Cannot create a temporary build dir ${WORKDIR}" >&2
    exit 1
fi

TARBALL_NAME="${1}"
ARCHIVE="${UBUILD_SOURCES_DIR}/${TARBALL_NAME}"
SRC_URI="http://ftp.gnu.org/gnu/gmp/${TARBALL_NAME}"
P="${TARBALL_NAME/.tar*}"
PN="gmp"
S="${WORKDIR}/${P}"
BUILD_DIR="${WORKDIR}/build"
T="${WORKDIR}/temp"
TARGET_DIR="${UBUILD_BUILD_DIR}/${PN}"
IMAGE_TARGET_DIR="${UBUILD_IMAGE_DIR}/${PN}"
BUILD_LOG="${T}/build.log"

export TMPDIR="${T}"
echo
echo "Ubuild environment variables:"
echo "UBUILD_BUILD_DIR: ${UBUILD_BUILD_DIR}"
echo "UBUILD_IMAGE_DIR: ${UBUILD_IMAGE_DIR}"
echo "UBUILD_SOURCES_DIR: ${UBUILD_SOURCES_DIR}"
echo "UBUILD_PATCHES: ${UBUILD_PATCHES}"
echo
echo "Local variables:"
echo "TARBALL_NAME: ${TARBALL_NAME}"
echo "ARCHIVE: ${ARCHIVE}"
echo "WORKDIR: ${WORKDIR}"
echo "BUILD_DIR: ${BUILD_DIR}"
echo "P: ${P}"
echo "PN: ${PN}"
echo "S: ${S}"
echo "BUILD_LOG: ${BUILD_LOG}"
echo

src_fetch() {
    if [ ! -f "${ARCHIVE}" ]; then
        echo "Starting to download ${ARCHIVE}"
        wget "${SRC_URI}" -O "${ARCHIVE}" || return 1
    else
        local sha1=$(sha1sum "${ARCHIVE}")
        echo "${ARCHIVE} already there, SHA1: ${sha1}"
    fi
}

src_unpack() {
    tar -x -a -f "${ARCHIVE}" -C "${WORKDIR}"
}

src_patch() {
    if [ -n "${UBUILD_PATCHES}" ]; then
        for p in ${UBUILD_PATCHES}; do

            echo "Applying patch: ${p}"
            local level=
            local good=
            for level in $(seq 0 5); do
                patch --quiet -p${level} --dry-run -f < "${p}" \
                    2>&1 > "${BUILD_LOG}" && {
                    good=1;
                    break;
                }
            done
            if [ "${good}" != "1" ]; then
                echo "Cannot apply patch ${p}" >&2
                return 1
            else
                patch --quiet -p${level} -f < "${p}"
            fi

        done
    fi
}

src_prepare() {
    mkdir -p "${T}"
    mkdir -p "${BUILD_DIR}"
    cd "${S}"
    src_patch
}

src_configure() {
    cd "${BUILD_DIR}"
    "${S}/configure" --prefix="/usr" --enable-cxx
}

src_compile() {
    cd "${BUILD_DIR}"
    make ${MAKEOPTS}
}

src_install() {
    cd "${BUILD_DIR}"
    make DESTDIR="${TARGET_DIR}" install
}

src_merge() {
    mkdir -p "${TARGET_DIR}"
    rsync -avx -H -A "${TARGET_DIR}"/ "${IMAGE_TARGET_DIR}"/
}

src_fetch
src_unpack
src_prepare
src_configure
src_compile
src_install
src_merge
