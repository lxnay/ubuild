#include base.beagleboard.header

[ubuild]
cache_dir = benchmark-base.armhf.beagleboard.cache/
cross_env = architecture_env/armhf/cross_env
build_dir = /var/tmp/ubuild.beagleboard-armhf-base.build
compile_dir = /var/tmp/ubuild.beagleboard-armhf-base.compile
image_name = benchmark.armhf-base.beagleboard.img.xz
env = architecture_env/armhf/env

[pkg=benchmark]
build = scripts/build_pkg_benchmark.sh
cache_vars = BENCHMARK_CFLAGS_CONFIG BENCHMARK_CFLAGS_MD5
env = benchmark_env/armhf-base
sources = SoundTest
url = http://lxnay.sabayon.org/ubuild/SoundTest.tar.gz

