#!/bin/bash

set -e

. build.include

# If all the tarballs are cached, we need to let this have
# a chance to run.
root_init
