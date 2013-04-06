#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2013 Fabio Erculiani
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
Tests for ubuild.
"""
import copy
import os
import shutil
import sys
import tempfile
import unittest
import ubuild


class UbuildSpecTest(unittest.TestCase):

    def _testSpecParse(self, spec_content, expected):
        """
        Test the UbuildSpec parser. This is a generic function that
        takes the content of a .spec file (spec_content is a string)
        and compares the parsed outcome with the expected metadata.

        spec_content is a format string, that can contain:
          - %(script)s for executable scripts
          - %(env)s for env files.
          - %(dir)s for empty directories.
        """
        tmp_fd, tmp_path = None, None
        spec_tmp_fd, spec_tmp_path = None, None
        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp(prefix="ubuild.test")
            tmp_fd, tmp_path = tempfile.mkstemp(prefix="ubuild.test")
            os.chmod(tmp_path, 0o700)
            spec_tmp_fd, spec_tmp_path = tempfile.mkstemp(
                prefix="ubuild.test.spec",
                suffix=".spec")

            repl_dict = {
                "script": tmp_path,
                "env": tmp_path,
                "dir": tmp_dir,
                }
            content = spec_content % repl_dict

            with os.fdopen(spec_tmp_fd, "w") as spec_f:
                spec_f.write(content)
            spec_tmp_fd = None

            parser = ubuild.SpecParser(spec_tmp_path)
            parser.read()

            def _repl_list(l):
                new_l = []
                for x in l:
                    if isinstance(x, (list, tuple)):
                        x = _repl_list(x)
                    elif isinstance(x, dict):
                        x = _repl_dict(x)
                    elif isinstance(x, int):
                        pass
                    else: # string
                        x = x % repl_dict
                    new_l.append(x)

                if isinstance(l, tuple):
                    new_l = tuple(new_l)
                return new_l

            def _repl_dict(d):
                new_d = {}
                for k, v in list(d.items()):
                    if isinstance(v, (list, tuple)):
                        v = _repl_list(v)
                    elif isinstance(v, dict):
                        v = _repl_dict(v)
                    elif isinstance(v, int):
                        pass
                    else: # string
                        v = v % repl_dict
                    new_d[k] = v
                return new_d

            expected_copy = _repl_dict(copy.deepcopy(expected))
            self.assertEqual(expected_copy, parser)

            return parser

        finally:
            if spec_tmp_fd is not None:
                try:
                    os.close(spec_tmp_fd)
                except OSError:
                    pass
            if spec_tmp_path is not None:
                os.remove(spec_tmp_path)
            if tmp_fd is not None:
                os.close(tmp_fd)
            if tmp_path is not None:
                os.remove(tmp_path)
            if tmp_dir is not None:
                shutil.rmtree(tmp_dir, True)

    def testSimpleSpec(self):
        """
        Test a simple .spec file parsing.
        """
        content = """
# This is an ubuild .spec file that aims to create
# an armel (armv7, softfp) image.

[ubuild]
build_dir = %(dir)s
build_image = %(script)s argA argB
cache_dir = %(dir)s
cache_vars = ARCH ABI GMPABI CROSS_SYSROOT
cache_vars = CFLAGS CPPFLAGS CXXFLAGS LDFLAGS
cache_vars = WORK_ROOTFS_DIR GCC_CONFIGURE_ARGS
cross_env = %(env)s
cross_post = %(script)s arg1 arg2
destination_dir = %(dir)s
env = %(env)s
image_name = ubuild_armel.test.img
pre = %(script)s pre1 pre2
rootfs_dir = %(dir)s
sources_dir = %(dir)s

[cross=gmp]
build = %(script)s a b c
patch = %(env)s
patch = %(env)s invalid
sources = %(dir)s
url = http://ftp.gnu.org/gnu/gmp/gmp-4.3.2.tar.bz2

[cross=mpfr]
build = %(script)s a
build = %(script)s b
build = %(script)s c
env = %(env)s
env = %(env)s
env = %(env)s
env = %(env)s
sources = %(dir)s
url = http://ftp.gnu.org/gnu/mpfr/mpfr-2.4.2.tar.bz2

[cross=mpc]
build = %(script)s d H d
build = %(script)s H H H
pre = %(script)s pre pre
pre = %(script)s pre pre pre
env = %(env)s
env = %(env)s
env = %(env)s invalid
sources = %(dir)s
url = ftp://gcc.gnu.org/pub/gcc/infrastructure/mpc-0.8.1.tar.gz

[cross=binutils]
build = %(script)s d e f
sources = %(dir)s
url = http://ftp.gnu.org/gnu/binutils/binutils-2.23.1.tar.gz

[cross=gcc-stage1]
build = %(script)s a
pre = %(script)s pre pre pre
pre = %(script)s pre pre
sources = %(dir)s
url = http://ftp.gnu.org/gnu/gcc/gcc-4.7.2/gcc-4.7.2.tar.bz2

[cross=linux-headers]
build = %(script)s
build = %(script)s
pre = %(script)s pre pre pre
post = %(script)s post post post
sources = %(dir)s
url = http://www.kernel.org/pub/linux/kernel/v3.x/linux-3.7.10.tar.xz
url = http://www.kernel.org/pub/linux/kernel/v3.x/linux-extras-1.2.3.tar.xz
url = http://www.kernel.org/pub/linux/kernel/v3.x/linux-more-1.2.3.tar.xz

[cross=glibc-ports]
build = %(script)s asd
patch = %(env)s
patch = %(env)s
post = %(script)s post ost st t
env = %(env)s
env = %(env)s
sources = %(dir)s
url = http://ftp.gnu.org/gnu/glibc/glibc-ports-2.16.0.tar.xz

[cross=glibc-headers]
build = %(script)s glibc-headers
patch = %(env)s
env = %(env)s
sources = %(dir)s
url = http://ftp.gnu.org/gnu/glibc/glibc-2.16.0.tar.xz foo.tar.gz

[cross=glibc]
build = %(script)s glibc
patch = %(env)s invalid
sources = %(dir)s
url = http://ftp.gnu.org/gnu/glibc/glibc-2.16.0.tar.xz glibc.tar.xz

[cross=gcc]
build = %(script)s gcc
sources = %(dir)s
url = http://ftp.gnu.org/gnu/gcc/gcc-4.7.2/gcc-4.7.2.tar.bz2

[pkg=kernel]
build = %(script)s kernel
cache_vars = KERNEL_DEFCONFIG KERNEL_CONFIG
sources = %(dir)s
url = http://www.kernel.org/pub/linux/kernel/v3.x/linux-3.7.10.tar.xz
"""
        expected = {
            "ubuild": {
                "pre": [
                    ["%(script)s", "pre1", "pre2"]
                ],
                "image_name": ["ubuild_armel.test.img"],
                "rootfs_dir": ["%(dir)s"],
                "cross_env": ["%(env)s"],
                "cross_post": [
                    ["%(script)s", "arg1", "arg2"]
                ],
                "sources_dir": ["%(dir)s"],
                "cache_vars": [
                    ["ARCH", "ABI", "GMPABI", "CROSS_SYSROOT"],
                    ["CFLAGS", "CPPFLAGS", "CXXFLAGS", "LDFLAGS"],
                    ["WORK_ROOTFS_DIR", "GCC_CONFIGURE_ARGS"],
                ],
                "build_image": [
                    ["%(script)s", "argA", "argB"]
                ],
                "build_dir": ["%(dir)s"],
                "cache_dir": ["%(dir)s"],
                "env": ["%(env)s"],
                "destination_dir": ["%(dir)s"]
            },
            "cross=gmp": {
                "url": [
                    (
                        "http://ftp.gnu.org/gnu/gmp/gmp-4.3.2.tar.bz2",
                        "gmp-4.3.2.tar.bz2"
                    )
                ],
                "build": [
                    ["%(script)s", "a", "b", "c"]
                ],
                "sources": ["%(dir)s"],
                "patch": ["%(script)s"]
            },
            "cross=mpc": {
                "pre": [
                    ["%(script)s", "pre", "pre"],
                    ["%(script)s", "pre", "pre", "pre"]
                ],
                "url": [
                    (
                        "ftp://gcc.gnu.org/pub/gcc/infrastructure/mpc-0.8.1.tar.gz",
                        "mpc-0.8.1.tar.gz"
                    )
                ],
                "build": [
                    ["%(script)s", "d", "H", "d"],
                    ["%(script)s", "H", "H", "H"]
                ],
                "sources": ["%(dir)s"],
                "env": ["%(env)s", "%(env)s"]
            },
            "cross=binutils": {
                "url": [
                    (
                        "http://ftp.gnu.org/gnu/binutils/binutils-2.23.1.tar.gz",
                        "binutils-2.23.1.tar.gz"
                    )
                ],
                "build": [
                    ["%(script)s", "d", "e", "f"]
                ],
                "sources": ["%(dir)s"],
            },
            "cross=gcc-stage1": {
                "pre": [
                    ["%(script)s", "pre", "pre", "pre"],
                    ["%(script)s", "pre", "pre"]
                ],
                "url": [
                    (
                        "http://ftp.gnu.org/gnu/gcc/gcc-4.7.2/gcc-4.7.2.tar.bz2",
                        "gcc-4.7.2.tar.bz2"
                    )
                ],
                "sources": ["%(dir)s"],
                "build": [
                    ["%(script)s", "a"],
                ]},
            "cross=glibc-headers": {
                "url": [
                    (
                        "http://ftp.gnu.org/gnu/glibc/glibc-2.16.0.tar.xz",
                        "foo.tar.gz"
                    )
                ],
                "build": [
                    ["%(script)s", "glibc-headers"]
                ],
                "sources": ["%(dir)s"],
                "env": ["%(env)s"],
                "patch": ["%(script)s"]
            },
            "cross=mpfr": {
                "url": [
                    (
                        "http://ftp.gnu.org/gnu/mpfr/mpfr-2.4.2.tar.bz2",
                        "mpfr-2.4.2.tar.bz2"
                    )
                ],
                "build": [
                    ["%(script)s", "a"],
                    ["%(script)s", "b"],
                    ["%(script)s", "c"]
                ],
                "sources": ["%(dir)s"],
                "env": [
                    "%(env)s",
                    "%(env)s",
                    "%(env)s",
                    "%(env)s"
                ]},
            "cross=linux-headers": {
                "pre": [
                    ["%(script)s", "pre", "pre", "pre"]
                ],
                "url": [
                    (
                        "http://www.kernel.org/pub/linux/kernel/v3.x/linux-3.7.10.tar.xz",
                        "linux-3.7.10.tar.xz"
                    ),
                    (
                        "http://www.kernel.org/pub/linux/kernel/v3.x/linux-extras-1.2.3.tar.xz",
                        "linux-extras-1.2.3.tar.xz"
                    ), (
                        "http://www.kernel.org/pub/linux/kernel/v3.x/linux-more-1.2.3.tar.xz",
                        "linux-more-1.2.3.tar.xz"
                    )],
                "post": [
                    ["%(script)s", "post", "post", "post"]
                ],
                "sources": ["%(dir)s"],
                "build": [
                    ["%(script)s"],
                    ["%(script)s"]
                ]},
            "pkg=kernel": {
                "url": [
                    (
                        "http://www.kernel.org/pub/linux/kernel/v3.x/linux-3.7.10.tar.xz",
                        "linux-3.7.10.tar.xz"
                    )],
                "build": [
                    ["%(script)s", "kernel"]
                ],
                "sources": ["%(dir)s"],
                "cache_vars": [
                    ["KERNEL_DEFCONFIG", "KERNEL_CONFIG"]
                ]},
            "cross=gcc": {
                "url": [
                    (
                        "http://ftp.gnu.org/gnu/gcc/gcc-4.7.2/gcc-4.7.2.tar.bz2",
                        "gcc-4.7.2.tar.bz2"
                    )],
                "sources": ["%(dir)s"],
                "build": [
                    ["%(script)s", "gcc"]
                ]},
            "cross=glibc-ports": {
                "url": [
                    (
                        "http://ftp.gnu.org/gnu/glibc/glibc-ports-2.16.0.tar.xz",
                        "glibc-ports-2.16.0.tar.xz"
                    )],
                "post": [
                    ["%(script)s", "post", "ost", "st", "t"]
                ],
                "sources": ["%(dir)s"],
                "build": [
                    ["%(script)s", "asd"]
                ],
                "env": ["%(env)s", "%(env)s"],
                "patch": ["%(script)s", "%(script)s"]
            },
            "cross=glibc": {
                "url": [
                    (
                        "http://ftp.gnu.org/gnu/glibc/glibc-2.16.0.tar.xz",
                        "glibc.tar.xz"
                    ),],
                "sources": ["%(dir)s"],
                "build": [
                    ["%(script)s", "glibc"]
                ]}
        }
        parser = self._testSpecParse(content, expected)

        cache_vars = [
            "ABI", "ARCH", "CFLAGS", "CPPFLAGS",
            "CROSS_SYSROOT", "CXXFLAGS", "GCC_CONFIGURE_ARGS",
            "GMPABI", "LDFLAGS", "WORK_ROOTFS_DIR"]
        self.assertEqual(cache_vars, parser.cache_vars())
        cache_vars = ["KERNEL_CONFIG", "KERNEL_DEFCONFIG"]
        self.assertEqual(cache_vars, parser.target_cache_vars("pkg=kernel"))
        self.assertRaises(KeyError, parser.target_cache_vars, "foobar")

        cross_targets = [
            "cross=gmp", "cross=mpfr", "cross=mpc",
            "cross=binutils", "cross=gcc-stage1", "cross=linux-headers",
            "cross=glibc-ports", "cross=glibc-headers", "cross=glibc",
            "cross=gcc"]
        self.assertEqual(cross_targets, parser.cross_targets())
        for target in cross_targets:
            self.assert_(target in parser)
            self.assertEqual([], parser.target_cache_vars(target))

        pkg_targets = ["pkg=kernel"]
        self.assertEqual(pkg_targets, parser.pkg_targets())
        self.assert_("pkg=kernel" in parser)
        self.assertEqual(["KERNEL_CONFIG", "KERNEL_DEFCONFIG"],
                         parser.target_cache_vars("pkg=kernel"))

        self.assertRaises(ubuild.SpecParser.MissingParametersError,
                          self._testSpecParse, "", {})

        self.assertEqual(parser.ubuild(), parser["ubuild"])

        test_meta = [
            "build_dir", "build_image", "cache_dir",
            "destination_dir", "image_name", "rootfs_dir",
            "sources_dir"
        ]
        for k in test_meta:
            self.assertEqual(getattr(parser, k)(),
                             parser.ubuild()[k][0])
        self.assertEqual(parser.image_name(), "ubuild_armel.test.img")


if __name__ == "__main__":
    unittest.main()
