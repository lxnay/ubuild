#!/bin/bash

. build.include || exit 1
. initramfs.include || exit 1

# If all the tarballs are cached, we need to let this have
# a chance to run.
root_init || exit 1


_setup_inittab() {
    local inittab="${1}"

    if [ -z "${IMAGE_TTY_DEV}" ]; then
        echo "IMAGE_TTY_DEV unset, cannot setup /etc/inittab" >&2
        return 1
    elif [ ! -f "${inittab}" ]; then
        echo "${inittab} does not exist" >&2
        return 1
    fi
    inittab_tty=$(basename "${IMAGE_TTY_DEV}")
    echo "${inittab_tty}::respawn:/sbin/getty -nl /sbin/autologin 115200 ${inittab_tty}" \
        >> "${inittab}" || return 1
}

_setup_securetty() {
    local securetty="${1}"

    if [ ! -f "${securetty}" ]; then
        echo "${securetty} does not exist" >&2
        return 1
    fi
    echo "${IMAGE_TTY_DEV}" >> "${securetty}" || return 1
}


# setup /etc/inittab
_setup_inittab "${WORK_ROOTFS_DIR}/etc/inittab" || exit 1
_setup_inittab "${WORK_INITRAMFS_ROOTFS_DIR}/etc/inittab" || exit 1

# setup /etc/securetty
_setup_securetty "${WORK_ROOTFS_DIR}/etc/securetty" || exit 1
_setup_securetty "${WORK_INITRAMFS_ROOTFS_DIR}/etc/securetty" || exit 1

# As per u-boot hardcoded variables
INITRAMFS_NAME="initramfs"
COMPRESSED_INITRAMFS="${WORK_ROOTFS_DIR}/boot/${INITRAMFS_NAME}.gz"
echo "Generating initramfs: ${COMPRESSED_INITRAMFS}"

WORKDIR=$(TMPDIR="${UBUILD_BUILD_DIR}" mktemp -d --suffix="initramfs")
if [ -z "${WORKDIR}" ]; then
    echo "Cannot create temporary directory inside ${UBUILD_BUILD_DIR}" >&2
    exit 1
fi

# Generate the initramfs
temp_initramfs="${WORKDIR}/${INITRAMFS_NAME}"
initramfs_generate "${WORK_ROOTFS_DIR}" "${temp_initramfs}" || exit 1
initramfs_gzip "${temp_initramfs}" "${COMPRESSED_INITRAMFS}" || exit 1
rm "${temp_initramfs}" || exit 1
initramfs_u-bootize "${COMPRESSED_INITRAMFS}" || exit 1
