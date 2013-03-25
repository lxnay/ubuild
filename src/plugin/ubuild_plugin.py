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
import logging.config
import os
import shlex

from molecule.compat import convert_to_unicode
from molecule.output import darkred, blue
from molecule.specs.skel import GenericExecutionStep, GenericSpec

import molecule.utils


class UbuildSpec(GenericSpec):

    PLUGIN_API_VERSION = 1

    # TODO: revisit this when a build system is in place
    _cfg_file = os.getenv("UBUILD_LOGGING_CFGFILE")
    if _cfg_file:
        logging.config.fileConfig(_cfg_file, disable_existing_loggers=False)
    else:
        logging.basicConfig()

    def __init__(self, spec_file):
        """
        UbuildSpec constructor.
        """
        super(UbuildSpec, self).__init__(spec_file)
        self._logger = logging.getLogger("ubuild.UbuildSpec")

    @staticmethod
    def require_super_user():
        """
        No super-user privileges are required by default.
        """
        return False

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
            "cross_build_pkg",
            "destination_dir",
            "image_name",
            "rootfs_dir",
            "sources_dir",
            ]

    def parameters(self):
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
            items = self._comma_separate(value)
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

                build_script = path_parser(param_name, build_script)
                if build_script is None:
                    continue
                if not os.path.isfile(build_script):
                    self._logger.warning(
                        "%s: not a file '%s' (from: '%s')",
                        param_name, build_script, item)
                    continue

                env_file = path_parser(param_name, env_file)
                if env_file is None:
                    continue
                if not os.path.isfile(env_file):
                    self._logger.warning(
                        "%s: not a file '%s' (from: '%s')",
                        param_name, env_file, item)
                    continue

                if not self._verify_executable_arguments([build_script]):
                    self._logger.warning(
                        "%s: not executable '%s' (from: '%s')",
                        param_name, build_script, item)
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
            items = self._comma_separate(value)
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

                patch = path_parser(param_name, patch)
                if patch is None:
                    continue
                if not os.path.isfile(patch):
                    self._logger.warning(
                        "%s: not a file '%s' (from: '%s')",
                        param_name, patch, item)
                    continue

                outcome.append({
                        "tarball": convert_to_unicode(tarball),
                        "patch": convert_to_unicode(patch),
                        })

            return outcome

        def path_parser(param_name, string):
            """
            Generate a valid path from a string, if possible.
            Take into account relative paths (relative to the .spec file)
            as well.
            If string is invalid or points to a non-existing directory,
            return None.
            """
            path = string.strip()
            if not path:
                self._logger.warning(
                    "%s: invalid parameter '%s'",
                    param_name, string)
                return None

            if os.path.isabs(path):
                return path

            base_dir = os.path.dirname(self._spec_file)
            return os.path.join(base_dir, path)

        def directory_verifier(param_name, value):
            """
            Validate value, must be a valid directory path string.
            """
            if value is None:
                return False

            if not os.path.isdir(value):
                self._logger.warning(
                    "%s: not a directory '%s'",
                    param_name, value)
                return False
            return True

        def create_directory_verifier(param_name, value):
            """
            Validate value, must be a valid directory path string.
            The directory will be created if it does not exist.
            """
            if value is None:
                return False

            if not os.path.isdir(value):
                try:
                    os.makedirs(value, 0o755)
                except OSError:
                    self._logger.exception(
                        "%s: cannot create directory: '%s'",
                        param_name, value)
                    return False
            return True

        def file_verifier(param_name, value):
            """
            Validate value, must be a valid file path string.
            """
            if value is None:
                return False

            if not os.path.isfile(value):
                self._logger.warning(
                    "%s: not a file '%s'",
                    param_name, value)
                return False
            return True

        def string_parser(param_name, string):
            """
            Parse a string, make sure it is non-empty (strip spaces and
            other non-printable chars first).
            """
            value = string.strip()
            if not value:
                self._logger.warning(
                    "%s: invalid parameter '%s'",
                    param_name, string)
                return ""
            return value

        def command_splitter(param_name, string):
            """
            Split a string into an argv list using shlex and complete
            the possibly relative path to the executable script using
            the .spec directory as the base path.
            """
            args = self._command_splitter(string)
            exe, other_args = args[0], args[1:]
            exe = path_parser(param_name, exe)
            if exe is None:
                return []

            other_args.insert(0, exe)
            return other_args

        def verify_argv0_executable(param_name, args):
            """
            Ensure that the first element of the list points to an
            existing file and it has the executable bits set.
            """
            if not args:
                self._logger.warning(
                    "%s: invalid parameter: ''",
                    param_name)
                return False

            is_exec = self._verify_executable_arguments(args)
            if not is_exec:
                self._logger.warning(
                    "%s: not found or not executable: '%s'",
                    param_name, args[0])
                return False
            return True


        return {
            "execution_strategy": {
                "verifier": lambda x: len(x) != 0,
                "parser": functools.partial(string_parser,
                                            "execution_strategy"),
                },
            "rootfs_dir": {
                "verifier": functools.partial(directory_verifier, "rootfs_dir"),
                "parser": functools.partial(path_parser, "rootfs_dir"),
                },
            "sources_dir": {
                "verifier": functools.partial(directory_verifier,
                                              "sources_dir"),
                "parser": functools.partial(path_parser, "sources_dir"),
                },
            "cache_dir": {
                "verifier": functools.partial(
                    create_directory_verifier, "cache_dir"),
                "parser": functools.partial(path_parser, "cache_dir"),
                },
            "cache_variables": {
                "verifier": lambda x: len(x) != 0,
                "parser": self._comma_separate,
                },
            "build_dir": {
                "verifier": functools.partial(
                    create_directory_verifier, "build_dir"),
                "parser": functools.partial(path_parser, "build_dir"),
                },
            "destination_dir": {
                "verifier": functools.partial(
                    create_directory_verifier, "destination_dir"),
                "parser": functools.partial(path_parser, "destination_dir"),
                },
            "image_name": {
                "verifier": lambda x: len(x) != 0,
                "parser": functools.partial(string_parser, "image_name"),
                },
            "cross_build_pkg": {
                "verifier": is_build_pkg,
                "parser": functools.partial(
                    build_pkg_splitter, "cross_build_pkg"),
                },
            "cross_patch_pkg": {
                "verifier": is_patch_pkg,
                "parser": functools.partial(
                    patch_pkg_splitter, "cross_patch_pkg"),
                },
            "cross_pre_build": {
                "verifier": functools.partial(verify_argv0_executable,
                                              "cross_pre_build"),
                "parser": functools.partial(command_splitter,
                                            "cross_pre_build"),
                },
            "cross_post_build": {
                "verifier": functools.partial(verify_argv0_executable,
                                              "cross_post_build"),
                "parser": functools.partial(command_splitter,
                                            "cross_post_build"),
                },
            "build_pkg": {
                "verifier": is_build_pkg,
                "parser": functools.partial(build_pkg_splitter, "build_pkg"),
                },
            "patch_pkg": {
                "verifier": is_patch_pkg,
                "parser": functools.partial(patch_pkg_splitter, "patch_pkg"),
                },
            "pre_build": {
                "verifier": functools.partial(verify_argv0_executable,
                                              "pre_build"),
                "parser": functools.partial(command_splitter, "pre_build"),
                },
            "post_build": {
                "verifier": functools.partial(verify_argv0_executable,
                                              "post_build"),
                "parser": functools.partial(command_splitter, "post_build"),
                },
            "build_image": {
                "verifier": functools.partial(verify_argv0_executable,
                                              "build_image"),
                "parser": functools.partial(command_splitter, "build_image"),
                },
            }

    def execution_steps(self):
        """
        Overridden from GenericSpec.
        """
        return [CrossToolchainHandler]

    def output(self, metadata):
        """
        Overridden from GenericSpec.
        """
        self._logger.debug(
            "%s, parsed metadata:",
            self._spec_file)
        for key in sorted(metadata.keys()):
            if key == "__plugin__":
                continue
            self._logger.debug(
                "%s: %s", key, metadata[key])


class BaseHandler(GenericExecutionStep):
    """
    Base class for all the Ubuild Molecule handlers.
    """

    def __init__(self, spec_path, metadata):
        super(BaseHandler, self).__init__(spec_path, metadata)
        self._logger = logging.getLogger("ubuild.Handler")

    def _base_environment(self, base_env):
        """
        Generate a base environment for child processes.
        The generated environment will inherit the given
        base_env dict.
        """
        env = base_env.copy()
        env_keys = (
            ("UBUILD_ROOTFS_DIR", "rootfs_dir"),
            ("UBUILD_SOURCES_DIR", "sources_dir"),
            ("UBUILD_CACHE_DIR", "cache_dir"),
            ("UBUILD_DESTINATION_DIR", "destination_dir"),
            ("UBUILD_IMAGE_NAME", "image_name"),
            )
        for env_var, env_meta in env_keys:
            value = self.metadata.get(env_meta)
            if value is not None:
                self._logger.debug(
                    "Setting %s=%s",
                    env_var, value)
                env[env_var] = value
            else:
                self._logger.warning(
                    "%s won't be set, becuse %s is unset",
                    env_var, env_meta)
        return env


class CrossToolchainHandler(BaseHandler):
    """
    Ubuild Molecule handler in charge of building the cross compiler
    toolchain.
    """

    def __init__(self, spec_path, metadata):
        """
        Object constructor.
        """
        super(CrossToolchainHandler, self).__init__(spec_path, metadata)
        self._build_dir = None

    def setup(self):
        """
        Overridden from GenericExecutionStep.
        """
        # TODO: generate build_dir and export it, self._build_dir
        

    def pre_run(self):
        """
        Overridden from GenericExecutionStep.
        """
        self._output.output("[%s|%s] %s" % (
                blue("CrossToolchainHandler"),
                darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        args = self.metadata.get("cross_pre_build")
        if not args:
            return 0

        env = self._base_environment(os.environ)
        self._output.output(
            "[%s|%s] %s: %s" % (
                blue("CrossToolchainHandler"),
                darkred(self.spec_name),
                _("spawning"),
                " ".join(args))
            )
        exit_st = molecule.utils.exec_cmd(args, env=env)
        self._output.output(
            "[%s|%s] %s: %s" % (
                blue("CrossToolchainHandler"),
                darkred(self.spec_name),
                _("exit status"),
                exit_st,
                )
            )
        return exit_st

    def run(self):
        """
        Overridden from GenericExecutionStep.
        """
        # TODO: complete

    def post_run(self):
        """
        Overridden from GenericExecutionStep.
        """
        self._output.output("[%s|%s] %s" % (
                blue("CrossToolchainHandler"),
                darkred(self.spec_name),
                _("executing post_run"),
            )
        )

        args = self.metadata.get("cross_post_build")
        if not args:
            return 0

        env = self._base_environment(os.environ)
        self._output.output(
            "[%s|%s] %s: %s" % (
                blue("CrossToolchainHandler"),
                darkred(self.spec_name),
                _("spawning"),
                " ".join(args))
            )
        exit_st = molecule.utils.exec_cmd(args, env=env)
        self._output.output(
            "[%s|%s] %s: %s" % (
                blue("CrossToolchainHandler"),
                darkred(self.spec_name),
                _("exit status"),
                exit_st,
                )
            )
        return exit_st

    def kill(self, success=True):
        """
        Overridden from GenericExecutionStep.
        """
