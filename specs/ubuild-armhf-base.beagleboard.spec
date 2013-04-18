# ubuild .spec file that creates an armel (armv7,
# hardfp) image for the BeagleBoard.

#include base.beagleboard.header

[ubuild]
build_dir = /var/tmp/ubuild.beagleboard-armhf.build_dir
compile_dir = /var/tmp/ubuild.beagleboard-armhf.compile_dir
cache_dir = beagleboard.armhf.cache/
image_name = armv7l.hardfp.BeagleBoard.img.xz
env = architecture_env/armhf/env
cross_env = architecture_env/armhf/cross_env
