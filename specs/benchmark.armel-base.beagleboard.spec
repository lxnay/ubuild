#include base.beagleboard.header

[ubuild]
cache_dir = benchmark-base.armel.beagleboard.cache/
cross_env = architecture_env/armel/cross_env
build_dir = /var/tmp/ubuild.beagleboard-armel-base.build
compile_dir = /var/tmp/ubuild.beagleboard-armel-base.compile
image_name = benchmark.armel-base.beagleboard.img.xz
env = architecture_env/armel/env

[pkg=benchmark]
build = scripts/build_pkg_benchmark.sh
cache_vars = BENCHMARK_CFLAGS_CONFIG BENCHMARK_CFLAGS_MD5
env = benchmark_env/armel-base
sources = SoundTest
url = http://lxnay.sabayon.org/ubuild/SoundTest.tar.gz

