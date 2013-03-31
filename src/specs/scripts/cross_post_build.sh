#!/bin/bash

set -e

. toolchain.include

# If all the tarballs are cached, we need to let this have
# a chance to run.
cross_sysroot_init
