#!/bin/bash

. build.include || exit 1

# If all the tarballs are cached, we need to let this have
# a chance to run.
root_init || exit 1

# This will be moved to the vfat partition at some point
echo "${UBOOT_UENV}" > "${WORK_ROOTFS_DIR}/boot/uEnv.txt" || exit 1
