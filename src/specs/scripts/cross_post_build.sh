#!/bin/bash

set -e

SUBDIR="${1}"
if [ -z "${SUBDIR}" ]; then
    echo "${0} <subdir containing env>" >&2
    exit 1
fi

. "${SUBDIR}/cross_env"

. toolchain.include

# If all the tarballs are cached, we need to let this have
# a chance to run.
cross_sysroot_init
