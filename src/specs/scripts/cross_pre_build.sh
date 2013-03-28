#!/bin/bash

set -e

SUBDIR="${1}"
if [ -z "${SUBDIR}" ]; then
    echo "${0} <subdir containing env>" >&2
    exit 1
fi

. "${SUBDIR}/cross_env"
. build.include

echo "Mirroring ${UBUILD_ROOTFS_DIR} into work rootfs dir: ${WORK_ROOTFS_DIR}/"

mkdir -p "${WORK_ROOTFS_DIR}"
/usr/bin/rsync -a -x -H -A -X --delete-during \
    "${UBUILD_ROOTFS_DIR}"/ "${WORK_ROOTFS_DIR}"/
