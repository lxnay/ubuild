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
"""Tests for ubuild_plugin."""
import copy
import os
import shutil
import sys
import tempfile
import unittest

from molecule.settings import SpecParser


class UbuildSpecTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from plugin import ubuild_plugin
        cls._ubuild = ubuild_plugin

    def testExecutionStrategy(self):
        """
        Ensure that UbuildSpec.execution_strategy()
        returns an expected value.
        """
        self.assertEqual(
            self._ubuild.UbuildSpec.execution_strategy(),
            "ubuild")

    def _testBuildPkg(self, meta):
        """
        Simple test to assert a correct {cross_,}build_pkg arguments evaluation.
        """
        tmp_fd, tmp_path = None, None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(prefix="ubuild.test")
            os.chmod(tmp_path, 0o700)

            income = """\
tarball.tar.xz foo,
tarball.tar.xz %(build_1)s %(env_1)s,
tarball.tar.xz "!this does not exist" "!even this",
tarball.tar.xz %(build_2)s %(env_2)s,
tarball.tar.xz,
""" % {
                "build_1": tmp_path,
                "build_2": tmp_path,
                "env_1": tmp_path,
                "env_2": tmp_path,}

            expected_outcome = [
                {
                    "tarball": "tarball.tar.xz",
                    "build_script": tmp_path,
                    "env_file": tmp_path,
                    },
                {
                    "tarball": "tarball.tar.xz",
                    "build_script": tmp_path,
                    "env_file": tmp_path,
                    },
                ]

            out = meta["parser"](income)
            self.assertEqual(expected_outcome, out)
            self.assertEqual(meta["verifier"](out), True)

        finally:
            if tmp_fd is not None:
                os.close(tmp_fd)
            if tmp_path is not None:
                os.remove(tmp_path)

    def testCrossBuildPkg(self):
        """
        Simple test to assert a correct cross_build_pkg arguments evaluation.
        """
        spec = self._ubuild.UbuildSpec("")
        data_path = spec.parameters()
        meta = data_path["cross_build_pkg"]
        self._testBuildPkg(meta)

    def testBuildPkg(self):
        """
        Simple test to assert a correct build_pkg arguments evaluation.
        """
        spec = self._ubuild.UbuildSpec("")
        data_path = spec.parameters()
        meta = data_path["build_pkg"]
        self._testBuildPkg(meta)

    def _testPatchPkg(self, meta):
        """
        Simple test to assert a correct {cross_,}patch_pkg arguments evaluation.
        """
        tmp_fd, tmp_path = None, None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(prefix="ubuild.test")
            os.chmod(tmp_path, 0o700)

            income = """\
tarball.tar.xz bar,
tarball.tar.xz %(patch_1)s,
tarball.tar.xz,
tarball.tar.xz %(patch_2)s,
tarball.tar.xz "!this does not exist",
""" % {
                "patch_1": tmp_path,
                "patch_2": tmp_path,}

            expected_outcome = [
                {
                    "tarball": "tarball.tar.xz",
                    "patch": tmp_path,
                    },
                {
                    "tarball": "tarball.tar.xz",
                    "patch": tmp_path,
                    },
                ]

            out = meta["parser"](income)
            self.assertEqual(expected_outcome, out)
            self.assertEqual(meta["verifier"](out), True)

        finally:
            if tmp_fd is not None:
                os.close(tmp_fd)
            if tmp_path is not None:
                os.remove(tmp_path)

    def testCrossPatchPkg(self):
        """
        Simple test to assert a correct cross_patch_pkg arguments evaluation.
        """
        spec = self._ubuild.UbuildSpec("")
        data_path = spec.parameters()
        meta = data_path["cross_patch_pkg"]
        self._testPatchPkg(meta)

    def testCrossPatchPkg(self):
        """
        Simple test to assert a correct patch_pkg arguments evaluation.
        """
        spec = self._ubuild.UbuildSpec("")
        data_path = spec.parameters()
        meta = data_path["patch_pkg"]
        self._testPatchPkg(meta)

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

            parser = SpecParser(spec_tmp_path)
            extracted = parser.parse()

            self.assert_(isinstance(extracted["__plugin__"],
                                    self._ubuild.UbuildSpec))
            extracted.pop("__plugin__")

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

            self.assertEqual(expected_copy, extracted)

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
        Test simple .spec file parsing.
        """
        content = """
# This is an ubuild molecule .spec file that aims to create
# an armel (armv7, softfp) image.

execution_strategy: ubuild

# Directory in where the build process will take place
build_dir: %(dir)s

# Directory in where builds are cached
cache_dir: %(dir)s

# Directory in where the final image will be placed
destination_dir: %(dir)s

# Name of the final system image
image_name: ubuild_armel.test.img

# Directory in where the source tarballs are expected to be found.
sources_dir: %(dir)s

# The base root filesystem directory, containing the base set of
# files that are expected to be found in the final image.
rootfs_dir: %(dir)s

cross_build_pkg:
    gmp-4.3.2.tar.bz2 %(script)s %(env)s,
    gcc-4.7.2.tar.bz2 %(script)s %(env)s

cross_patch_pkg:
    gmp-4.3.2.tar.bz2 %(script)s,
    gcc-4.7.2.tar.bz2 %(script)s

build_pkg:
    glibc-2.17.tar.bz2 %(script)s %(env)s,
    busybox-1.0.tar.bz2 %(script)s %(env)s

patch_pkg:
    glibc-2.17.tar.bz2 %(script)s,
    busybox-1.0.tar.bz2 %(script)s

cache_variables:
    CFLAGS, CPPFLAGS, CXXFLAGS, LDFLAGS,
    ARCH, ABI, GMPABI, MAKEOPTS

cross_pre_build: %(script)s armel_cross_pre

cross_post_build: %(script)s armel_cross_post

pre_build: %(script)s armel_pre

post_build: %(script)s armel_post

build_image: %(script)s armel
"""
        expected = {
            'cross_post_build': [
                '%(script)s',
                'armel_cross_post'],
            'build_image': [
                '%(script)s',
                'armel'],
            'image_name': 'ubuild_armel.test.img',
            'execution_strategy': 'ubuild',
            'cache_dir': '%(dir)s',
            'cross_pre_build': [
                '%(script)s',
                'armel_cross_pre'],
            'patch_pkg': [
                {
                    'tarball': 'glibc-2.17.tar.bz2',
                    'patch': '%(script)s'
                    },
                {
                    'tarball': 'busybox-1.0.tar.bz2',
                    'patch': '%(script)s'
                    }
                ],
            'build_pkg': [
                {
                    'tarball': 'glibc-2.17.tar.bz2',
                    'build_script': '%(script)s',
                    'env_file': '%(env)s'
                    },
                {
                    'tarball': 'busybox-1.0.tar.bz2',
                    'build_script': '%(script)s',
                    'env_file': '%(env)s'
                    }
                ],
            'rootfs_dir': '%(dir)s',
            'post_build': [
                '%(script)s',
                'armel_post'],
            'destination_dir': '%(dir)s',
            'pre_build': [
                '%(script)s', 'armel_pre'],
            'sources_dir': '%(dir)s',
            'build_dir': '%(dir)s',
            'cross_build_pkg': [
                {
                    'tarball': 'gmp-4.3.2.tar.bz2',
                    'build_script': '%(script)s',
                    'env_file': '%(env)s'
                    },
                {
                    'tarball': 'gcc-4.7.2.tar.bz2',
                    'build_script': '%(script)s',
                    'env_file': '%(env)s'
                    }
                ],
            'cross_patch_pkg': [
                {
                    'tarball': 'gmp-4.3.2.tar.bz2',
                    'patch': '%(script)s'
                    },
                {
                    'tarball': 'gcc-4.7.2.tar.bz2',
                    'patch': '%(script)s'
                    }
                ],
            'cache_variables': [
                'CFLAGS', 'CPPFLAGS', 'CXXFLAGS',
                'LDFLAGS', 'ABI', 'ARCH', 'GMPABI',
                'MAKEOPTS']
            }
        self._testSpecParse(content, expected)


if __name__ == "__main__":
    module_dir = os.path.join(
        os.path.dirname(__file__), "..")
    sys.path.insert(0, module_dir)

    # This is a fallback molecule path
    molecule_dir = os.path.join(module_dir, "..")
    sys.path.append(molecule_dir)

    # this tests what the ubuild script does
    plugins = ["plugin.ubuild_plugin"]
    os.environ["MOLECULE_PLUGIN_MODULES"] = ":".join(plugins)

    unittest.main()
