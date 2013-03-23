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
Tests for ubuild_plugin.
"""
import os
import sys
import tempfile
import unittest


class UbuildSpecTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import ubuild_plugin
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

            out = meta["ve"](income)
            self.assertEqual(expected_outcome, out)
            self.assertEqual(meta["cb"](out), True)

        finally:
            if tmp_fd is not None:
                os.close(tmp_fd)
            if tmp_path is not None:
                os.remove(tmp_path)

    def testCrossBuildPkg(self):
        """
        Simple test to assert a correct cross_build_pkg arguments evaluation.
        """
        spec = self._ubuild.UbuildSpec()
        data_path = spec.parser_data_path()
        meta = data_path["cross_build_pkg"]
        self._testBuildPkg(meta)

    def testBuildPkg(self):
        """
        Simple test to assert a correct build_pkg arguments evaluation.
        """
        spec = self._ubuild.UbuildSpec()
        data_path = spec.parser_data_path()
        meta = data_path["build_pkg"]
        self._testBuildPkg(meta)

    def _testPatchPkg(self, meta):
        """
        Simple test to assert a correct {cross_,}patch_pkg arguments evaluation.
        """
        tmp_fd, tmp_path = None, None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(prefix="ubuild.test")

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

            out = meta["ve"](income)
            self.assertEqual(expected_outcome, out)
            self.assertEqual(meta["cb"](out), True)

        finally:
            if tmp_fd is not None:
                os.close(tmp_fd)
            if tmp_path is not None:
                os.remove(tmp_path)

    def testCrossPatchPkg(self):
        """
        Simple test to assert a correct cross_patch_pkg arguments evaluation.
        """
        spec = self._ubuild.UbuildSpec()
        data_path = spec.parser_data_path()
        meta = data_path["cross_patch_pkg"]
        self._testPatchPkg(meta)

    def testCrossPatchPkg(self):
        """
        Simple test to assert a correct patch_pkg arguments evaluation.
        """
        spec = self._ubuild.UbuildSpec()
        data_path = spec.parser_data_path()
        meta = data_path["patch_pkg"]
        self._testPatchPkg(meta)


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
