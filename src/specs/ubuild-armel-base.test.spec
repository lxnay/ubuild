# This is an ubuild molecule .spec file that aims to create
# an armel (armv7, softfp) image.

execution_strategy: ubuild

# Directory in where the build process will take place
build_dir: /var/tmp/ubuild_build

# Directory in where builds are cached
cache_dir: cache/

# Directory in where the final image will be placed
destination_dir: /var/tmp/ubuild_out

# Name of the final system image
image_name: ubuild_armel.test.img

# Directory in where the source tarballs are expected to be found.
sources_dir: sources/

# The base root filesystem directory, containing the base set of
# files that are expected to be found in the final image.
rootfs_dir: rootfs/

cross_build_pkg:
    gmp gmp-4.3.2.tar.bz2 scripts/cross_gmp.sh scripts/armel/cross_env,
    mpfr mpfr-2.4.2.tar.bz2 scripts/cross_mpfr.sh scripts/armel/cross_env,
    mpc mpc-0.8.1.tar.gz scripts/cross_mpc.sh scripts/armel/cross_env,
    binutils binutils-2.23.1.tar.gz scripts/cross_binutils.sh scripts/armel/cross_env,
    gcc-stage1 gcc-4.7.2.tar.bz2 scripts/cross_gcc-stage1.sh scripts/armel/cross_env,
    linux-headers linux-3.7.10.tar.xz scripts/cross_linux-headers.sh scripts/armel/cross_env,
    glibc-ports glibc-ports-2.16.0.tar.xz scripts/cross_glibc-ports.sh scripts/armel/cross_env,
    glibc-headers glibc-2.16.0.tar.xz scripts/cross_glibc-headers.sh scripts/armel/cross_env,
    glibc glibc-2.16.0.tar.xz scripts/cross_glibc.sh scripts/armel/cross_env,
    gcc gcc-4.7.2.tar.bz2 scripts/cross_gcc-stage2.sh scripts/armel/cross_env,

cross_patch_pkg:
    gmp patches/gmp-4.3.2-ABI-multilib.patch,
    glibc patches/glibc-2.16-no-libgcc_s.patch,
    glibc-ports patches/glibc-ports-2.16-no-libgcc_s.patch,
    glibc-ports patches/glibc-ports-2.16-arm-specific-static-stubs.patch,

build_pkg:
    kernel linux-3.7.10.tar.xz scripts/build_pkg_kernel.sh scripts/armel/env,

cache_variables:
    CFLAGS, CPPFLAGS, CXXFLAGS, LDFLAGS,
    ARCH, ABI, GMPABI, CROSS_SYSROOT,
    WORK_ROOTFS_DIR, GCC_CONFIGURE_ARGS,
    KERNEL_DEFCONFIG, KERNEL_CONFIG

cross_post_build: scripts/cross_post_build.sh armel

pre_build: scripts/pre_build.sh

build_image: scripts/build_image.sh armel

# TODO, add:
# - {build,patch}_pkg
