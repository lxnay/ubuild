#!/bin/bash

. build.include || exit 1

# If all the tarballs are cached, we need to let this have
# a chance to run.
root_init || exit 1

# This will be moved to the vfat partition at some point
if [ ! -e "${UBOOT_UENV}" ]; then
    echo "${UBOOT_UENV} does not exist" >&2
    exit 1
fi
echo "uEnv.txt content:"
echo "--"
cat "${UBOOT_UENV}"
echo "--"
cat "${UBOOT_UENV}" > "${WORK_ROOTFS_DIR}/boot/uEnv.txt" || exit 1
