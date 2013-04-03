#!/bin/bash

. build.include || exit 1

# If all the tarballs are cached, we need to let this have
# a chance to run.
root_init || exit 1
