#!/bin/sh

[ "$ACTION" = add ] && [ "$MODALIAS" != "" ] && /sbin/modprobe $MODALIAS
[ "$ACTION" = remove ] && [ "$MODALIAS" != "" ] && /sbin/modprobe -r $MODALIAS
/sbin/mdev $@

