#!/bin/bash

. build.include || exit 1

# If all the tarballs are cached, we need to let this have
# a chance to run.
root_init || exit 1

# TODO: dev nodes? cannot create them if unprivileged

# setup /etc/inittab
inittab="${WORK_ROOTFS_DIR}/etc/inittab"
if [ -z "${IMAGE_TTY_DEV}" ]; then
    echo "IMAGE_TTY_DEV unset, cannot setup /etc/inittab" >&2
    exit 1
elif [ ! -f "${inittab}" ]; then
    echo "${inittab} does not exist" >&2
    exit 1
fi
echo "${IMAGE_TTY_DEV}::respawn:/sbin/getty -nl /sbin/autologin 115200 ${IMAGE_TTY_DEV}" \
    >> "${inittab}" || exit 1

# setup /etc/securetty
securetty="${WORK_ROOTFS_DIR}/etc/securetty"
if [ ! -f "${securetty}" ]; then
    echo "${securetty} does not exist" >&2
    exit 1
fi
echo "${IMAGE_TTY_DEV}" >> "${securetty}" || exit 1

# As per u-boot hardcoded variables
INITRAMFS_NAME="initramfs"
COMPRESSED_INITRAMFS="${WORK_ROOTFS_DIR}/boot/${INITRAMFS_NAME}.gz"
echo "Generating initramfs: ${COMPRESSED_INITRAMFS}"

WORKDIR=$(TMPDIR="${UBUILD_BUILD_DIR}" mktemp -d --suffix="initramfs")
if [ -z "${WORKDIR}" ]; then
    echo "Cannot create temporary directory inside ${UBUILD_BUILD_DIR}" >&2
    exit 1
fi

# Generate the cpio archive.
temp_initramfs="${WORKDIR}/${INITRAMFS_NAME}"
make_cpio "${WORK_ROOTFS_DIR}" "${temp_initramfs}" || exit 1
gzip -c "${temp_initramfs}" > "${COMPRESSED_INITRAMFS}" || exit 1
rm "${temp_initramfs}" || exit 1

mkimage -A arm -O linux -T ramdisk -C none -a "${UBOOT_RAMDISK_ADDRESS}" \
    -e "${UBOOT_RAMDISK_ENTRYPOINT}" -d "${COMPRESSED_INITRAMFS}" \
    "${COMPRESSED_INITRAMFS}.u-boot" || exit 1
mv "${COMPRESSED_INITRAMFS}.u-boot" "${COMPRESSED_INITRAMFS}" || exit 1
