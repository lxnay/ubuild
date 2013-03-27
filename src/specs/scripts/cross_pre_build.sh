#!/bin/bash

set -e

SUBDIR="${1}"
if [ -z "${SUBDIR}" ]; then
    echo "${0} <subdir containing cross_build_env>" >&2
    exit 1
fi

. "${SUBDIR}/cross_build_env"

echo "Mirroring ${UBUILD_ROOTFS_DIR} into sysroot: ${SYSROOT}/"

mkdir -p "${SYSROOT}"
/usr/bin/rsync -a -v -x -H -A -X --delete-during \
    "${UBUILD_ROOTFS_DIR}"/ "${SYSROOT}"/
