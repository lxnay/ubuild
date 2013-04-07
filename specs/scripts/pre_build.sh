#!/bin/bash

. build.include || exit 1

echo "Mirroring ${UBUILD_ROOTFS_DIR} into work rootfs dir: ${WORK_ROOTFS_DIR}/"

mkdir -p "${WORK_ROOTFS_DIR}" || exit 1
/usr/bin/rsync -a -x -H -A -X --delete-during \
    "${UBUILD_ROOTFS_DIR}"/ "${WORK_ROOTFS_DIR}"/ || exit 1

echo -n "Mirroring ${UBUILD_INITRAMFS_ROOTFS_DIR} into work initramfs"
echo "rootfs dir: ${WORK_INITRAMFS_ROOTFS_DIR}/"

mkdir -p "${WORK_INITRAMFS_ROOTFS_DIR}" || exit 1
/usr/bin/rsync -a -x -H -A -X --delete-during \
    "${UBUILD_INITRAMFS_ROOTFS_DIR}"/ \
    "${WORK_INITRAMFS_ROOTFS_DIR}"/ || exit 1
