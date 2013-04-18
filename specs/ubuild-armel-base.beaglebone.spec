# ubuild .spec file that creates an armel (armv7,
# softfp) image for the BeagleBone.

#include base.beaglebone.header

[ubuild]
build_dir = /var/tmp/ubuild.beaglebone-armel.build_dir
compile_dir = /var/tmp/ubuild.beaglebone-armel.compile_dir
cache_dir = beaglebone.armel.cache/
image_name = armv7l.softfp.BeagleBone.img.xz
env = architecture_env/armel/env
cross_env = architecture_env/armel/cross_env
