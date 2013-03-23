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

import functools
import logging
import shlex

from molecule.compat import convert_to_unicode
from molecule.specs.skel import GenericSpec


class UbuildSpec(GenericSpec):

    PLUGIN_API_VERSION = 0
    logging.basicConfig()

    def __init__(self):
        """
        UbuildSpec constructor.
        """
        super(UbuildSpec, self).__init__()
        self._logger = logging.getLogger("ubuild.UbuildSpec")

    @staticmethod
    def execution_strategy():
        """
        Return the execution strategy required by .spec
        files in order to be handled by this plugin.
        """
        return "ubuild"

    def vital_parameters(self):
        """
        Return a list of parameters that must be declared
        in the .spec file and thus, are considered mandatory.
        """
        return [
            "build_dir",
            "build_pkg",
            "cross_build_pkg",
            "destination_dir",
            "image_name",
            "rootfs_dir",
            "sources_dir",
            ]

    def parser_data_path(self):
        """
        Formal definition of the .spec file supported parameters.
        """

        def is_build_pkg(value):
            """
            Determine if {cross_,}build_pkg metadata is valid.
            """
            if value:
                return True
            return False

        def build_pkg_splitter(param_name, value):
            """
            Generate the metadata from a {cross_,}build_pkg parameter.
            """
            outcome = []
            items = self.valid_comma_sep_list(value)
            if not items:
                return outcome

            for item in items:
                elems = shlex.split(item)
                if len(elems) != 3:
                    self._logger.warning(
                        "%s: invalid line: '%s'",
                        param_name, item)
                    continue
                tarball, build_script, env_file = elems

                if not self.valid_exec(build_script):
                    self._logger.warning(
                        "%s: not executable or not found '%s' (from: '%s')",
                        param_name, build_script, item)
                    continue

                if not self.valid_file(env_file):
                    self._logger.warning(
                        "%s: not a file '%s' (from: '%s')",
                        param_name, env_file, item)
                    continue

                outcome.append({
                        "tarball": convert_to_unicode(tarball),
                        "build_script": convert_to_unicode(build_script),
                        "env_file": convert_to_unicode(env_file),
                        })

            return outcome

        def is_patch_pkg(value):
            """
            Determine if {cross_,}patch_pkg metadata is valid.
            """
            if value:
                return True
            return False

        def patch_pkg_splitter(param_name, value):
            """
            Generate the metadata from a {cross_,}patch_pkg parameter.
            """
            outcome = []
            items = self.valid_comma_sep_list(value)
            if not items:
                return outcome

            for item in items:
                elems = shlex.split(item)
                if len(elems) != 2:
                    self._logger.warning(
                        "%s: invalid line: '%s'",
                        param_name, item)
                    continue
                tarball, patch = elems

                if not self.valid_file(patch):
                    self._logger.warning(
                        "%s: not a file '%s' (from: '%s')",
                        param_name, patch, item)
                    continue

                outcome.append({
                        "tarball": convert_to_unicode(tarball),
                        "patch": convert_to_unicode(patch),
                        })

            return outcome

        return {
            "execution_strategy": {
                "cb": self.ne_string,
                "ve": self.ve_string_stripper,
                },
            "rootfs_dir": {
                "cb": self.valid_dir,
                "ve": self.ve_string_stripper,
                },
            "sources_dir": {
                "cb": self.valid_dir,
                "ve": self.ve_string_stripper,
                },
            "cache_dir": {
                "cb": self.valid_dir,
                "ve": self.ve_string_stripper,
                },
            "cache_variables": {
                "cb": self.ne_string,
                "ve": self.ve_string_splitter,
                },
            "build_dir": {
                "cb": self.valid_path_string,
                "ve": self.ve_string_stripper,
                },
            "destination_dir": {
                "cb": self.valid_path_string,
                "ve": self.ve_string_stripper,
                },
            "image_name": {
                "cb": self.ne_string,
                "ve": self.ve_string_stripper,
                },
            "cross_build_pkg": {
                "cb": is_build_pkg,
                "ve": functools.partial(build_pkg_splitter, "cross_build_pkg"),
                },
            "cross_patch_pkg": {
                "cb": is_patch_pkg,
                "ve": functools.partial(patch_pkg_splitter, "cross_patch_pkg"),
                },
            "cross_pre_build": {
                "cb": self.valid_exec_first_list_item,
                "ve": self.ve_command_splitter,
                },
            "cross_post_build": {
                "cb": self.valid_exec_first_list_item,
                "ve": self.ve_command_splitter,
                },
            "build_pkg": {
                "cb": is_build_pkg,
                "ve": functools.partial(build_pkg_splitter, "build_pkg"),
                },
            "patch_pkg": {
                "cb": is_patch_pkg,
                "ve": functools.partial(patch_pkg_splitter, "patch_pkg"),
                },
            "pre_build": {
                "cb": self.valid_exec_first_list_item,
                "ve": self.ve_command_splitter,
                },
            "post_build": {
                "cb": self.valid_exec_first_list_item,
                "ve": self.ve_command_splitter,
                },
            "build_image": {
                "cb": self.valid_exec_first_list_item,
                "ve": self.ve_command_splitter,
                },
            }
