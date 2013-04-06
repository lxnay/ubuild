#!/bin/bash
# This script must respect the env variables:
# - UBUILD_IMAGE_NAME: the output file name image to create
# - UBUILD_DESTINATION_DIR: the directory in where the image must be saved
#
# This tool needs:
# dd, fdisk, sfdisk, losetup

. build.include || exit 1

export LC_ALL=en_US.UTF-8
export PATH="${PATH}:/usr/sbin"
export TMPDIR="${UBUILD_BUILD_DIR}"

# Boot partition type
BOOT_PART_TYPE="${BOOT_PART_TYPE:-vfat}"
BOOT_PART_TYPE_MBR="${BOOT_PART_TYPE_MBR:-0x0C}"
BOOT_PART_MKFS_ARGS="${BOOT_PART_MKFS_ARGS:--n boot -F 32}"
# Root partition type
ROOT_PART_TYPE="${ROOT_PART_TYPE:-ext3}"
ROOT_PART_MKFS_ARGS="${ROOT_PART_MKFS_ARGS:--L Linux}"

# Image parameters
CMP_FILE="${UBUILD_DESTINATION_DIR}/${UBUILD_IMAGE_NAME}"
FILE_EXT="${1}"
if [ -z "${FILE_EXT}" ]; then
    echo "Image extension not passed as first argument" >&2
    echo "No compression will be used" >&2
    FILE="${CMP_FILE}"
elif [ "${FILE_EXT}" = ".xz" ]; then
    FILE="${CMP_FILE%${FILE_EXT}}"
    COMPRESSOR="xz -v"
elif [ "${FILE_EXT}" = ".gz" ]; then
    FILE="${CMP_FILE%${FILE_EXT}}"
    COMPRESSOR="gzip"
elif [ "${FILE_EXT}" = ".bz2" ]; then
    FILE="${CMP_FILE%${FILE_EXT}}"
    COMPRESSOR="bzip2"
else
    echo "Unsupported ${FILE_EXT} compression, aborting" >&2
    exit 1
fi


SIZE="${IMAGE_SIZE_MB}"
BOOT_DIR="${WORK_ROOTFS_DIR}/boot"


cleanup_loopbacks() {
    cd /
    sync
    sleep 5
    sync
    [ -n "${tmp_file}" ] && rm "${tmp_file}" 2> /dev/null
    [ -n "${tmp_dir}" ] && {
        ${PRIV_AGENT} umount "${tmp_dir}/proc" &> /dev/null;
    }
    [ -n "${tmp_dir}" ] && {
        ${PRIV_AGENT} umount "${tmp_dir}" &> /dev/null;
        rmdir "${tmp_dir}" &> /dev/null;
    }
    [ -n "${boot_tmp_dir}" ] && {
        ${PRIV_AGENT} umount "${boot_tmp_dir}" &> /dev/null;
        rmdir "${boot_tmp_dir}" &> /dev/null;
    }
    sleep 1
    [ -n "${boot_part}" ] && losetup -d "${boot_part}" 2> /dev/null
    [ -n "${root_part}" ] && losetup -d "${root_part}" 2> /dev/null
    [ -n "${DRIVE}" ] && losetup -d "${DRIVE}" 2> /dev/null
}
trap "cleanup_loopbacks" 1 2 3 6 9 14 15 EXIT

# Erase the file
echo "Generating the empty image file at ${FILE}"
dd if=/dev/zero of="${FILE}" bs=1024000 count="${SIZE}" || exit 1

DRIVE=$(losetup -f "${FILE}" --show)
if [ -z "${DRIVE}" ]; then
    echo "Cannot execute losetup for ${FILE}" >&2
    exit 1
fi

echo "Configured the loopback partition at ${DRIVE}"
# Calculate size using fdisk
SIZE=$(fdisk -l "${DRIVE}" | grep Disk | grep bytes | awk '{print $5}')
CYLINDERS=$((SIZE/255/63/512))
# Magic first partition size, given 9 cylinders below
MAGICSIZE="73995264"
STARTOFFSET="32256"

echo "Disk size    : ${SIZE} bytes"
echo "Disk cyls    : ${CYLINDERS}"
echo "Magic size   : ${MAGICSIZE} bytes (boot part size)"
echo "Start offset : ${STARTOFFSET} bytes"

# this will create a first partition that is 73995264 bytes long
# Starts at sect 63, ends at sect 144584, each sector is 512bytes
# In fact it creates 9 cyls
{
echo ,9,${BOOT_PART_TYPE_MBR},*
echo ,,,-
} | sfdisk -D -H 255 -S 63 -C ${CYLINDERS} ${DRIVE}

sleep 2

# The second partiton will start at block 144585, get the end block
ENDBLOCK=$(fdisk -l "${DRIVE}" | grep "${DRIVE}p2" | awk '{print $3}')
EXTSIZE=$(((ENDBLOCK - 144585) * 512))
# Get other two loopback devices first
EXTOFFSET=$((STARTOFFSET + MAGICSIZE))

echo "Root part size   : ${EXTSIZE} bytes"
echo "Root part offset : ${EXTOFFSET} bytes"

# Get other two loopback devices first
boot_part=$(losetup -f --offset "${STARTOFFSET}" \
    --sizelimit "${MAGICSIZE}" "${FILE}" --show)
if [ -z "${boot_part}" ]; then
    echo "Cannot setup the boot partition loopback" >&2
    exit 1
fi

root_part=$(losetup -f --offset "${EXTOFFSET}" \
    --sizelimit "${EXTSIZE}" "${FILE}" --show)
if [ -z "${root_part}" ]; then
    echo "Cannot setup the ${ROOT_PART_TYPE} partition loopback" >&2
    exit 1
fi

echo "Boot Partiton at  : ${boot_part}"
echo "Root Partition at : ${root_part}"

# Format boot
echo "Formatting ${BOOT_PART_TYPE} ${boot_part}..."
"mkfs.${BOOT_PART_TYPE}" ${BOOT_PART_MKFS_ARGS} "${boot_part}" || exit 1

# Format extfs
echo "Formatting ${ROOT_PART_TYPE} ${root_part}..."
"mkfs.${ROOT_PART_TYPE}" ${ROOT_PART_MKFS_ARGS} "${root_part}" || exit 1

boot_tmp_dir=$(mktemp -d --suffix=boot.mount)
if [ -z "${boot_tmp_dir}" ]; then
    echo "Cannot create temporary dir (boot)" >&2
    exit 1
fi
chmod 755 "${boot_tmp_dir}" || exit 1

tmp_dir=$(mktemp -d --suffix=root.mount)
if [[ -z "${tmp_dir}" ]]; then
    echo "Cannot create temporary dir" >&2
    exit 1
fi
chmod 755 "${tmp_dir}" || exit 1

sync

echo "Setting up the boot directory content, mounting on ${boot_tmp_dir}"
${PRIV_AGENT} mount "${boot_part}" "${boot_tmp_dir}"
for item in "MLO" "uEnv.txt" "${UBOOT_IMAGE_NAME}"; do
    cp "${BOOT_DIR}/${item}" "${boot_tmp_dir}"/ || exit 1
done

echo "Setting up the root partition directory content, mounting on ${tmp_dir}"
${PRIV_AGENT} mount "${root_part}" "${tmp_dir}"
rsync -a -v -x -H -A -X "${WORK_ROOTFS_DIR}"/ "${tmp_dir}"/ || exit 1

${PRIV_AGENT} umount "${boot_tmp_dir}" || exit 1
${PRIV_AGENT} umount "${tmp_dir}" || exit 1

cleanup_loopbacks

# compress the image
if [ -n "${FILE_EXT}" ]; then
    echo "Compressing ${FILE} into ${CMP_FILE}"
    cat "${FILE}" | ${COMPRESSOR} > "${CMP_FILE}" || exit 1
    rm "${FILE}" || exit 1
fi

echo "Your MMC image ${CMP_FILE} is ready"
