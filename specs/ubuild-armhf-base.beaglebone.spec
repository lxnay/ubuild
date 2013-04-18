# ubuild .spec file that creates an armel (armv7,
# hardfp) image for the BeagleBone.

#include base.beaglebone.header

[ubuild]
build_dir = /var/tmp/ubuild.beaglebone-armhf.build_dir
compile_dir = /var/tmp/ubuild.beaglebone-armhf.compile_dir
cache_dir = beaglebone.armhf.cache/
image_name = armv7l.hardfp.BeagleBone.img.xz
env = architecture_env/armhf/env
cross_env = architecture_env/armhf/cross_env
