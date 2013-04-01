ubuild design
=============

TL;DR ubuild is a toolkit for building embedded system images based on
the Linux kernel.

It standardizes and eases the process of generating bootable images
for such systems, such as those based on the ARM architecture family.

Exposing the image creation process through a set of configurable
parameters makes it possible to benchmark, and in general test, an
embedded system under different build conditions.

The limited horse power offered by these systems, if compared to x86
standards, renders performance tuning through compile flags,
performance tests of specific changes and regression/integration
testing of a specific patch both non-trivial and not entirely
insignificant in terms of gained (or lost) performance.

ubuild is composed of several different components, as detailed
throughout this document.

The first usable version of ubuild aims to create a portable (running
a generic POSIX compliant OS is a strict requirement) toolkit for
building bootable images on an x86 system, using a cross-compiler.

An additional requirement is that it should be possible to build
everything (including the cross-compiler) from sources.

The problem of bootstrapping a new architecture is a common one
through the embedded systems developers. Unfortunately, none of the
open source tools available at the time of this writing aims to be as
flexible as ubuild in the long term (including buildroot).

The need of squeezing all the possible power out of an embedded system
CPU is real and generally done through manual and time consuming trial
and error.

Given the complexity of this task, also due to the high amount of
possible combinations to test and the potential use of experimental
flags, that could give major performance improvements at the price of
stability issues under corner cases, developers generally accept to
live with standard, stable compiler flags that unfortunately generate
much slower code.

Improving the situation by making it easier to automatically roll out
different images, with different compile settings is certainly
something beneficial for developers.

Furthermore, optimized code can lead to lower power consumption of the
system itself, because it improves the average efficiency
(MFLOPS/Watt), which is another pursued goal.

## Architecture

The ubuild architecture comprises the following components.

### ubuild core

Ubuild works by parsing .ini-like configuration files containing the
instructions to build a working system image.

The ubuild core is Python-based application that implements the
configuration file parsing and activity execution for building a
bootable embedded system, which includes the building of the cross
compilation toolchain (for instance and in random order: gcc, libc,
binutils, linux kernel headers, etc), a Linux kernel (including an
initramfs), and a minimal userspace system (busybox %2B C library),
including a starting root filesystem image (which may contain /etc
configuration files and other stuff like this).

ubuild core and its set of supported features will not change
dramatically over time and, most importantly, is not expected to break
the compatibility with older versions of configuration files.

The core however, has no notion about what kind of packages are part
of the toolchain, which is something delegated to the external build
scripts (read on to know more).

The configuration files syntax, as mentioned above, is like the
typical .ini files one, with the following improvements:

    1.  a section ([section]) can be defined multiple times.
    2.  sections are processed in the same order they are defined.
    3.  parameters in each section are in form of key = value, key can
        be defined multiple times and the set of values with the same key
        will form an ordered list (in the order of definition).


This is the list of the initial configuration file parameters
supported by the ubuild:

*  General configuration parameters, to be defined under the
[ubuild] section:

  1.  **rootfs_dir**: the base root filesystem directory, containing the
  base set of files that are expected to be found in the final
  image. Must be defined once. Exported as environment variable:
  UBUILD\_ROOTFS\_DIR.

  2.  **sources_dir**: the directory in where the source tarballs are
  expected to be found. Exported as environment variable:
  UBUILD\_SOURCES\_DIR.

  3.  **cache_dir**: the directory in where built binaries are stored
  for future retrieval. This aims to cache the building of binaries in
  order to speed up the image build process. The cache will try to take
  into consideration build related flags during the validation
  process. Exported as environment variable: UBUILD\_CACHE\_DIR. If no
  cache_dir is provided, the whole caching system will be disabled.

  4.  **cache_vars**: a comma separated list of environment variables
  considered for cache_dir elements validation. For instance: LDFLAGS,
  CFLAGS, ...

  5.  **build_dir**: the directory in where the build process will take
  place, all the temporary data and build-related binaries (such as the
  cross compiler) will be placed there. Must be defined, if the
  directory is not found, it will be created. Exported as environment
  variable: UBUILD\_BUILD\_DIR. This is passed to {cross\_,}build\_pkg
  arguments appending an extra sub-directory as the UBUILD\_IMAGE\_DIR,
  any {cross\_,}build\_pkg script is expected to copy the compiled files
  there as well to make the transparent build caching system work.

  6.  **destination_dir**: destination directory in where the final
  system image will be placed. Must be defined, if the directory is not
  found, it will be created. Exported as environment variable:
  UBUILD\_DESTINATION\_DIR.

  7.  **cross_pre**: a path pointing to a script (including its
  arguments) that will be always executed before starting the build
  process of the cross compiler targets is complete (even in case of
  build cache hits!). All the environment variables exported in
  cross_env will be passed. The executable must return a zero exit
  status or the ubuild execution will be aborted.

  8.  **cross_post**: a path pointing to a script (including its
  arguments) that will be always executed after the build process of the
  cross compiler targets is complete (even in case of build cache
  hits!). All the environment variables exported in cross_env will be
  passed. The executable must return a zero exit status or the ubuild
  execution will be aborted.

  9.  **pre**: a path pointing to a script (including its arguments)
  that will be always executed before starting the build process of the
  non-cross compiler targets is complete (even in case of build cache
  hits!). All the environment variables exported in env will be
  passed. The executable must return a zero exit status or the ubuild
  execution will be aborted.

  10. **post**: a path pointing to a script (including its arguments)
  that will be always executed after the build process of the non-cross
  compiler targets is complete (even in case of build cache hits!). All
  the environment variables exported in env will be passed. The
  executable must return a zero exit status or the ubuild execution will
  be aborted.

  11. **cross_env**: a file containing environment variable (that must
  be exported) that is sourced by ubuild for build cache validation of
  [cross=] section targets (changing variable values there may trigger a
  rebuild depending on the cache_vars value). Can be defined multiple
  times. These variables will be part of the environment passed to the
  [cross=] section build scripts.

  12. **env**: a file containing environment variable (that must be
  exported) that is sourced by ubuild for build cache validation of
  [pkg=] section targets (changing variable values there may trigger a
  rebuild depending on the cache_vars value). Can be defined multiple
  times. These variables will be part of the environment passed to the
  [pkg=] section build scripts.

  13. **image_name**: name of the final system image. Must be
  defined. Exported as environment variable: UBUILD\_IMAGE\_NAME.


*  For building the initial cross compiler, to be defined under the [cross=]
section:

  1.  section header [cross=]: target is the name of the build target,
  exported to the build script via the UBUILD\_TARGET\_NAME environment
  variable.

  2.  **url**: the URL from where the tarball is downloaded (no spaces
  allowed), plus, optionally, the name to use to store the tarball in
  the local sources\_dir (to avoid collisions). Can be defined multiple
  times. It is exported to the build script via the UBUILD\_SRC\_URI
  environment variable, semicolon separated: “ ; ”. The tarball file
  names are used to determine if the binaries have been already built
  and cached into ${UBUILD\_CACHE_DIR}/. Multiple tarballs must be
  unpacked (by the ubuild build scripts) into the same “work” directory.

  3.  **sources**: tarballs are unpacked into the same directory, this
  parameter defines which sub directory is the one containing the
  sources to build. Must be defined once, exported as UBUILD_SOURCES.

  4.  **build**: the executable (including its arguments) to launch to build
  the target. Can be defined multiple times. The executable is run with
  the current directory set to its parent directory. The executable must
  return a zero exit status or the ubuild execution will be aborted.

  5.  **patch**: a path to a patch to apply against the sources. Can be
  defined multiple times. The list of patches declared are passed to the
  build scripts environment variable: UBUILD_PATCHES. The list is space
  separated. Also see the build_dir description.

  6.  **env**: a file containing environment variable (that must be
  exported) that is sourced by ubuild for build cache validation
  (changing variable values there may trigger a rebuild depending on the
  cache_vars value). Can be defined multiple times (the [ubuild]
  cross_env is sourced first). These variables will be part of the
  environment passed to the build scripts.

  7.  **cache_vars**: a space separated list of environment variables that
  are used to determine if the cached objects in the build cache are
  valid and, if not or not present, trigger the build scripts.

  8.  **pre**: a path pointing to a script (including its arguments) that
  will be always executed before starting the build process of this
  target (even in case of build cache hits!). All the environment
  variables exported in env will be passed. The executable must return a
  zero exit status or the ubuild execution will be aborted.

  9.  **post**: a path pointing to a script (including its arguments) that
  will be always executed after the build process of this target is
  complete (even in case of build cache hits!). All the environment
  variables exported in env will be passed. The executable must return a
  zero exit status or the ubuild execution will be aborted.


*  For building binaries with the cross compiler:

  1.  section header [pkg=]: target is the name of the build target,
  exported to the build script via the UBUILD\_TARGET\_NAME environment
  variable.

  2.  The rest of the parameters are the same of those defined in the
  [cross=] section.


*  For building the final image:

  1.  build_image: a path pointing to a script (including its arguments)
  that will be executed to produce the final image. This script must
  respect the UBUILD\_IMAGE\_NAME and UBUILD\_DESTINATION\_DIR
  environment variables.

### Build scripts

The architecture, toolchain dependent part of ubuild is left outside
the ubuild core. The build scripts is the place in where the
implementation details are defined. They are called by ubuild core
passing the parameters parsed from the configuration file, which the
user is in charge to write.

The set of build scripts initially supported will be geared towards
the creation of bootable ARMv7 memory card images and in particular,
towards working images for the BeagleBoard and PandaBoard.

### Cache

In order to speedup the build process, the ubuild core provides a
transparent, coarse-grained caching system. However, only the most
important variables are considered in the cache key, thus for cache
validation: only the variables defined in the cache_variables
parameter and some other internal ones are used to generate the cache
key. The lookup process works like this:

  1.  The environment files are parsed and environment variables
  retrieved. This list is filtered basing on cache_variables. Internal
  variables are added to the list, with their values.

  2.  A SHA1 checksum is generated using the list of filtered variables
  generated in the previous step.

  3.  A file starting with the given hash and ending with the tarball
  name is searched into cache_dir.

If the file is found, it will be uncompressed into the appropriate
location (depending if the tarball is coming either from
cross\_pkg\_build or pkg_build).

  1.  If the file is not found, the build script is called.
  2.  If the build script completes successfully, the outcome of the
  build is compressed and saved into cache_dir with the cache file
  name previously generated. The outcome is then moved to its final
  destination.
