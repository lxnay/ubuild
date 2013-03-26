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

import errno
import functools
import hashlib
import logging
import logging.config
import os
import shlex
import shutil
import subprocess
import tempfile

from molecule.compat import convert_to_unicode
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
            "build_image",
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
            return os.path.normpath(os.path.join(base_dir, path))

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
                "parser": lambda x: sorted(self._comma_separate(x)),
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


class UbuildCache(object):
    """
    Ubuild compilation cache class.

    This class is responsible of maintaining the compilation
    cache of tarballs built through Ubuild. In particular,
    it implements:

    - a lookup method to determine if the tarball is in cache.
      The cache key is generated by taking into consideration
      a set of elements: the tarball name, the sourced environment
      (from the environment file) and the list of patches and
      their checksums.
    - a pack method that takes an image directory as input (together
      with the parameters passed to lookup) and creates an entry in
      the cache directory (basically, it creates a tarball there).
    - an unpack method that takes an empty directory and a cache file
      as input and populates it.
    """

    def __init__(self, cache_dir, variables):
        """
        Object constructor.

        Args:
          cache_dir: the cache directory in where all the cached
              tarballs are to be found.
          variables: the environment variables used for cache validation.
        """
        self._dir = cache_dir
        self._vars = variables

    def _sha1(self, path):
        """
        Calculate a SHA1 hash of given file at path.

        Args:
          path: a file path.

        Returns:
          a SHA1 hash.
        """
        m = hashlib.sha1()
        with open(path, "rb") as readfile:
            block = readfile.read(16384)
            while block:
                m.update(block)
                block = readfile.read(16384)
        return m.hexdigest()

    def _generate_entry_name(self, tarball_name, patches, environment):
        """
        Given a set of input information, generate a cache entry file name.
        """
        sha = hashlib.sha1()
        sha.update(tarball_name)

        for patch in patches:
            sha.update(self._sha1(patch))

        for k in self._vars:
            v = environment.get(k, "")
            sha.update("%s=%s\n" % (k, v))

        entry_name = "%s_%s.tar.xz" % (tarball_name, sha.hexdigest(),)
        entry_path = os.path.abspath(os.path.join(self._dir, entry_name))
        return entry_path

    def lookup(self, tarball_name, patches, environment):
        """
        Execute a cache lookup. Return a path to a tarball file.

        Args:
          tarball_name: name of the source tarball.
          patches: list of patches to apply.
          environment: current build environment.

        Returns:
          a valid file path.
        """
        entry_path = self._generate_entry_name(
            tarball_name, patches, environment)

        if os.path.isfile(entry_path):
            return entry_path

    def pack(self, image_dir, tarball_name, patches, environment):
        """
        Compress the build directory into a tarball and place it
        into the cache directory.

        Args:
          image_dir: the directory in where the tarball has been built.
          tarball_name: name of the source tarball.
          patches: list of patches to apply.
          environment: current build environment.

        Returns:
          An exit status.
        """
        entry_path = self._generate_entry_name(
            tarball_name, patches, environment)

        args = ("tar", "-c", "-J", "-p", "-f", entry_path, "./")
        exit_st = subprocess.call(args, cwd=image_dir)
        return exit_st

    def unpack(self, unpack_dir, cache_file):
        """
        Unpack a cache file (returned by lookup()) into the given directory.

        Args:
          build_dir: the directory in where the tarball will be unpacked.
          cache_file: the compressed cache file.

        Returns:
          An exit status.
        """
        exit_st = subprocess.call(
            ("tar", "-x", "-J", "-f", cache_file),
            cwd=unpack_dir)
        return exit_st


class BaseHandler(GenericExecutionStep):
    """
    Base class for all the Ubuild Molecule handlers.
    """

    def __init__(self, spec_path, metadata):
        super(BaseHandler, self).__init__(spec_path, metadata)
        self._logger = logging.getLogger("ubuild.Handler")

        cache_dir = self.metadata.get("cache_dir")
        if cache_dir is not None:
            cache_vars = self.metadata.get("cache_variables")
            if cache_vars is not None:
                self._cacher = UbuildCache(cache_dir, cache_vars)
            else:
                self._logger.warning(
                    "Ubuild Cache disabled because cache_variables is unset")
                self._cacher = None
        else:
            self._logger.warning(
                "Ubuild Cache disabled because cache_dir is unset")
            self._cacher = None

    def _setup_environment(self, base_env):
        """
        Generate a base environment for child processes.
        The generated environment will inherit the given
        base_env dict.

        Args:
          base_env: the base environment.
        """
        env = base_env.copy()
        env_keys = (
            ("UBUILD_BUILD_DIR", "build_dir"),
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

    def _env_source(self, env_file):
        """
        Source the environment file and build a dict containing
        the environment variables set by it.
        Return None if environment file cannot be sourced.

        Args:
          env_file: the environment file to source.

        Returns:
          an environment dict.
        """
        env_sourcer = os.path.join(
            os.path.dirname(__file__),
            "env_sourcer.sh")
        assert os.path.isfile(env_sourcer)

        self._logger.info(
            "[%s] sourcing: %s", self.spec_name, env_file)
        args = (env_sourcer, env_file)
        tmp_fd, tmp_path = None, None

        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=self.metadata["build_dir"],
                prefix="ubuild._source")

            exit_st = subprocess.call(args, stdout=tmp_fd, env={})
            if exit_st != 0:
                return None

            # this way buffers are flushed out
            os.close(tmp_fd)
            tmp_fd = None
            env = {}

            with open(tmp_path, "r") as tmp_r:
                line = tmp_r.readline()

                while line:
                    params = line.rstrip().split("=", 1)
                    if len(params) == 2:
                        var, value = params
                        env[var] = value
                    line = tmp_r.readline()

            return env

        finally:
            if tmp_fd is not None:
                try:
                    os.close(tmp_fd)
                except OSError:
                    pass
            if tmp_path is not None:
                try:
                    os.remove(tmp_path)
                except OSError as err:
                    if err.errno != errno.ENOENT:
                        raise


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
        self._base_env = os.environ.copy()

    def setup(self):
        """
        Overridden from GenericExecutionStep.
        """
        return 0

    def pre_run(self):
        """
        Overridden from GenericExecutionStep.
        """
        args = self.metadata.get("cross_pre_build")
        if not args:
            return 0

        self._logger.info(
            "[%s] spawning: %s",
            self.spec_name,
            " ".join(args)
            )

        env = self._setup_environment(self._base_env)
        exit_st = subprocess.call(args, env=env)

        log_func = self._logger.info
        if exit_st != 0:
            log_func = self._logger.error
        log_func(
            "[%s] exit status: %d",
            self.spec_name,
            exit_st
            )
        return exit_st

    def run(self):
        """
        Overridden from GenericExecutionStep.
        """
        patch_pkgs = self.metadata.get("cross_patch_pkg", [])
        build_pkgs = self.metadata.get("cross_build_pkg", [])

        # From this O(m*n) mostruosity, generate a fast hash table
        # that has the tarball name as key and a list of patches as
        # value.
        patches_map = {}
        for build_pkg in build_pkgs:
            for patch_pkg in patch_pkgs:
                if build_pkg["tarball"] == patch_pkg["tarball"]:
                    obj = patches_map.setdefault(build_pkg["tarball"], [])
                    patch = os.path.abspath(patch_pkg["patch"])
                    obj.append(patch)

        for build_pkg in build_pkgs:
            tarball = build_pkg["tarball"]
            script = build_pkg["build_script"]
            env_file = build_pkg["env_file"]
            patches = patches_map.get(tarball, [])

            try:
                image_dir = tempfile.mkdtemp(
                    dir=self.metadata["build_dir"],
                    prefix=".ubuild_image.")
            except (OSError, IOError):
                self._logger.exception(
                    "CrossToolchainHandler: cannot create image_dir")
                return 1

            self._logger.info(
                "[%s] building: %s", self.spec_name, tarball)
            self._logger.info("  build script: %s", script)
            self._logger.info("  environment file: %s", env_file)

            file_env = self._env_source(env_file)
            base_env = self._base_env.copy()
            base_env.update(file_env)

            env = self._setup_environment(base_env)
            self._logger.debug("Setting UBUILD_IMAGE_DIR=%s", image_dir)
            env["UBUILD_IMAGE_DIR"] = image_dir

            patches_str = " ".join(patches)
            if patches_str:
                self._logger.debug("Setting UBUILD_PATCHES='%s'", patches_str)
                env["UBUILD_PATCHES"] = patches_str

            cache_file = None
            if self._cacher:
                cache_file = self._cacher.lookup(
                    tarball, patches, env)

            if cache_file:
                self._logger.info(
                    "[%s] Build of %s cached to %s",
                    self.spec_name, tarball, cache_file)
                exit_st = self._cacher.unpack(
                    self.metadata["build_dir"], cache_file)
                if exit_st != 0:
                    self._logger.error(
                        "[%s] unpack of %s failed with exit status: %d",
                        self.spec_name, cache_file, exit_st)
                    return exit_st

            else:
                args = (script, tarball)
                script_dir = os.path.dirname(script)
                exit_st = subprocess.call(args, env=env, cwd=script_dir)

                log_func = self._logger.info
                if exit_st != 0:
                    log_func = self._logger.error
                log_func("[%s] exit status: %d", self.spec_name, exit_st)
                if exit_st != 0:
                    return exit_st

                if self._cacher:

                    # ensure that the build script has moved the content
                    # to UBUILD_IMAGE_DIR.
                    try:
                        content = os.listdir(image_dir)
                    except (OSError, IOError):
                        self._logger.exception(
                            "Cannot get content of %s", image_dir)
                        content = None
                    if not content:
                        self._logger.error(
                            "[%s] %s built files have not been "
                            "moved to UBUILD_IMAGE_DIR, script: %s",
                            self.spec_name, tarball, script)
                        return 1

                    exit_st = self._cacher.pack(
                        image_dir, tarball, patches, env)
                    if exit_st != 0:
                        self._logger.error(
                            "[%s] pack of %s failed with exit status: %d",
                            self.spec_name, tarball, exit_st)
                        # ignore failure.

            self._logger.info("")

        return 0

    def post_run(self):
        """
        Overridden from GenericExecutionStep.
        """
        args = self.metadata.get("cross_post_build")
        if not args:
            return 0

        self._logger.info(
            "[%s] spawning: %s",
            self.spec_name,
            " ".join(args)
            )

        env = self._setup_environment(self._base_env)
        exit_st = subprocess.call(args, env=env)

        log_func = self._logger.info
        if exit_st != 0:
            log_func = self._logger.error
        log_func(
            "[%s] exit status: %d",
            self.spec_name,
            exit_st
            )
        return exit_st

    def kill(self, success=True):
        """
        Overridden from GenericExecutionStep.
        """
        return 0
