# This is an ubuild .spec file that aims to create
# an armel (armv7, softfp) image for the BeagleBone

[ubuild]
build_dir = /var/tmp/ubuild_build
build_image = scripts/build_image.sh
cache_dir = cache/
cache_vars = ARCH ABI GMPABI CROSS_SYSROOT
cache_vars = CFLAGS CPPFLAGS CXXFLAGS LDFLAGS
cache_vars = WORK_ROOTFS_DIR GCC_CONFIGURE_ARGS
cross_env = scripts/armel/cross_env
cross_post = scripts/cross_post_build.sh
destination_dir = /var/tmp/ubuild_out
env = scripts/armel/env
env = scripts/armel/beaglebone_env
image_name = ubuild_armel.test.img
pre = scripts/pre_build.sh
post = scripts/post_build.sh
rootfs_dir = rootfs/
sources_dir = sources/

[cross=gmp]
build = scripts/cross_gmp.sh
sources = gmp-4.3.2
patch = patches/gmp-4.3.2-ABI-multilib.patch
url = http://ftp.gnu.org/gnu/gmp/gmp-4.3.2.tar.bz2

[cross=mpfr]
build = scripts/cross_mpfr.sh
sources = mpfr-2.4.2
url = http://ftp.gnu.org/gnu/mpfr/mpfr-2.4.2.tar.bz2

[cross=mpc]
build = scripts/cross_mpc.sh
sources = mpc-0.8.1
url = ftp://gcc.gnu.org/pub/gcc/infrastructure/mpc-0.8.1.tar.gz

[cross=binutils]
build = scripts/cross_binutils.sh
sources = binutils-2.23.1
url = http://ftp.gnu.org/gnu/binutils/binutils-2.23.1.tar.gz

[cross=gcc-stage1]
build = scripts/cross_gcc-stage1.sh
sources = gcc-4.7.2
url = http://ftp.gnu.org/gnu/gcc/gcc-4.7.2/gcc-4.7.2.tar.bz2

[cross=linux-headers]
build = scripts/cross_linux-headers.sh
sources = linux-3.7.10
url = http://www.kernel.org/pub/linux/kernel/v3.x/linux-3.7.10.tar.xz

[cross=glibc-ports]
build = scripts/cross_glibc-ports.sh
patch = patches/glibc-ports-2.16-arm-specific-static-stubs.patch
patch = patches/glibc-ports-2.16-no-libgcc_s.patch
sources = glibc-ports-2.16.0
url = http://ftp.gnu.org/gnu/glibc/glibc-ports-2.16.0.tar.xz

[cross=glibc-headers]
build = scripts/cross_glibc-headers.sh
patch = patches/glibc-2.16-no-libgcc_s.patch
sources = glibc-2.16.0
url = http://ftp.gnu.org/gnu/glibc/glibc-2.16.0.tar.xz

[cross=glibc]
build = scripts/cross_glibc.sh
patch = patches/glibc-2.16-no-libgcc_s.patch
sources = glibc-2.16.0
url = http://ftp.gnu.org/gnu/glibc/glibc-2.16.0.tar.xz

[cross=gcc]
build = scripts/cross_gcc-stage2.sh
sources = gcc-4.7.2
url = http://ftp.gnu.org/gnu/gcc/gcc-4.7.2/gcc-4.7.2.tar.bz2

[pkg=kernel]
build = scripts/build_pkg_kernel.sh
cache_vars = KERNEL_DEFCONFIG KERNEL_CONFIG KERNEL_MD5
sources = linux-3.7.10
url = http://www.kernel.org/pub/linux/kernel/v3.x/linux-3.7.10.tar.xz

[pkg=u-boot]
build = scripts/build_pkg_u-boot.sh
cache_vars = UBOOT_DEFCONFIG UBOOT_UENV
post = scripts/post_build_uEnv.sh
sources = u-boot-2013.01.01
url = git://git.denx.de/u-boot.git@v2013.01.01 u-boot-2013.01.01.tar.gz

[pkg=busybox]
build = scripts/build_pkg_busybox.sh
cache_vars = BUSYBOX_DEFCONFIG BUSYBOX_CONFIG BUSYBOX_MD5
patch = patches/busybox/busybox-1.20.2-glibc-sys-resource.patch
patch = patches/busybox/busybox-1.7.4-signal-hack.patch
post = scripts/post_build_initramfs.sh
sources = busybox-1.20.2
url = http://www.busybox.net/downloads/busybox-1.20.2.tar.bz2

