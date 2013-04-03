#!/bin/bash

set -e

. build.include

echo "Mirroring ${UBUILD_ROOTFS_DIR} into work rootfs dir: ${WORK_ROOTFS_DIR}/"

mkdir -p "${WORK_ROOTFS_DIR}"
/usr/bin/rsync -a -x -H -A -X --delete-during \
    "${UBUILD_ROOTFS_DIR}"/ "${WORK_ROOTFS_DIR}"/
