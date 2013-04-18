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

import argparse
import codecs
import errno
import hashlib
import logging
import logging.config
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile


class SpecPreprocessor(object):

    PREFIX = "#"

    class PreprocessorError(Exception):
        """ Error while preprocessing file """

    def __init__(self, spec_path, encoding):
        self._spec_path = spec_path
        self._encoding = encoding
        self._expanders = {
            self.PREFIX + "include": self._include_expander,
        }

    def _recursive_expand(self, line):
        """
        Expand supported preprocessor statements recursively.

        Args:
          line: line to parse and expand, if needed.

        Returns:
          the expanded line.
        """
        split_line = line.lstrip().split(None, 1)
        if split_line:
            expander = self._expanders.get(split_line[0])
            if expander is not None:
                try:
                    line = expander(line)
                except RuntimeError as err:
                    raise SpecPreprocessor.PreprocessorError(
                        "invalid preprocessor line: %s" % (err,))
        return line

    def _include_expander(self, line):
        """
        Expand, recursively, an #include <path> statement.

        Args:
          line: line to parse and expand, if needed.

        Returns:
          the expanded line.
        """
        rest_line = line.split(None, 1)[1].strip()
        if not rest_line:
            return line

        if rest_line.startswith(os.path.sep):
            # absolute path
            path = rest_line
        else:
            path = os.path.join(os.path.dirname(self._spec_path),
                rest_line)

        if not (os.path.isfile(path) and os.access(path, os.R_OK)):
            raise SpecPreprocessor.PreprocessorError(
                "invalid preprocessor line: %s" % (line,))

        with codecs.open(path, "r", encoding=self._encoding) as spec_f:
            lines = None
            for line in spec_f.readlines():
                # call recursively
                line = self._recursive_expand(line)
                if lines is None:
                    lines = line
                else:
                    lines += line

        return lines + "\n"

    def parse(self):
        """
        Parse the file and expand all the supported preprocessor statements.

        Returns:
          the parsed file content string.
        """
        content = []
        with codecs.open(self._spec_path, "r",
                         encoding=self._encoding) as spec_f:
            for line in spec_f.readlines():
                line = self._recursive_expand(line)
                content.append(line)

        final_content = []
        for line in content:
            split_line = line.split(None, 1)
            if split_line:
                expander = self._expanders.get(split_line[0])
                if expander is not None:
                    line = expander(line)
            final_content.append(line)

        return ("".join(final_content)).split("\n")


class _SpecParser(dict):
    """
    Ubuild .ini-like configuration file parser.

    This is a base class useful for implementing .ini-like
    configuration files.

    A possible syntax is something like:

    [section]
    param = value
    param = value

    [section]
    param = value
    param = value
    """
    # Regular expression to match new configuration file sections.
    _SECTION_RE = re.compile(r"^\[(.*)\]$")

    # Starting character that denotes an ignored line.
    _COMMENT_CHAR = "#"

    # key <-> value statements separator.
    _SEPARATOR = "="

    # Must be reimplemented by subclasses.
    # Must be a list of supported statement keys.
    _SUPPORTED_KEYS = None

    def __init__(self, spec_file, encoding = None):
        super(_SpecParser, self).__init__()
        if encoding is None:
            encoding = "UTF-8"
        self._encoding = encoding
        self._logger = logging.getLogger("ubuild.SpecParser")
        self._ordered_sections = []
        self._spec_file = spec_file

    def read(self):
        """
        Read the given list of configuration file paths and populate
        the repository metadata.
        """
        self._parse(self._spec_file)

    def path(self):
        """
        Return the .spec file path.
        """
        return os.path.abspath(self._spec_file)

    def _parse(self, path):
        """
        Given a file path, parse the content and update the
        dictionary.

        Args:
          path: a configuration file path.

        Raises:
          SpecPreprocessor.PreprocessorError: if the file contains
          invalid preprocessor staments.
        """
        preproc = SpecPreprocessor(path, self._encoding)
        try:
            content = preproc.parse()
        except SpecPreprocessor.PreprocessorError as err:
            self._logger.error(
                "[%s] preprocessor error: %s", path, err)
            raise

        section_name = None
        supported_keys = None
        for line in content:

            line = line.strip()
            if not line:
                continue
            if line.startswith(self._COMMENT_CHAR):
                continue

            section = self._SECTION_RE.match(line)
            if section:
                candidate = self._validate_section(section)
                if candidate:
                    section_name = candidate
                    if candidate not in self._ordered_sections:
                        self._ordered_sections.append(candidate)

                    supported_keys_found = False
                    for s_k, k_d in self._SUPPORTED_KEYS.items():
                        if re.match(s_k, section_name):
                            supported_keys = k_d
                            supported_keys_found = True
                            break
                    if not supported_keys_found:
                        supported_keys = None
                        self._logger.warning(
                            "section [%s] is not recognized",
                            section_name)
                continue

            if section_name is None:
                self._logger.debug(
                    "ignoring line '%s', no section defined",
                    line)
                continue

            if supported_keys is None:
                self._logger.debug(
                    "ignoring line '%s' in unsupported section [%s]",
                    line, section_name)
                continue

            key_value = line.split(self._SEPARATOR, 1)
            if len(key_value) != 2:
                self._logger.warning(
                    "unsupported line '%s' in section [%s]",
                    line, section_name)
                continue

            key, value = [x.strip() for x in key_value]

            if key not in supported_keys:
                # key is invalid
                self._logger.warning(
                    "unsupported parameter '%s' in section [%s]",
                    key, section_name)
                continue

            mangler = supported_keys[key]
            orig_value = value
            if value and mangler is not None:
                value = mangler(path, section_name, key, value)

            if not value:
                self._logger.warning(
                    "invalid value '%s' for parameter '%s' in section [%s]",
                    orig_value, key, section_name)
                continue

            section_data = self.setdefault(section_name, {})
            key_data = section_data.setdefault(key, [])
            key_data.append(value)

    @classmethod
    def _validate_section(cls, match):
        """
        Validate a matched section object and return the
        extracted data (if valid) or None (if not valid).

        Args:
          match: a re.match object.

        Returns:
          the valid section name, if any, or None.
        """
        raise NotImplementedError()


class SpecParser(_SpecParser):
    """
    Ubuild .ini-like .spec files parser.

    This is an example of the supported syntax:

    [ubuild] # main and general ubuild .spec file section
    rootfs_dir = some/path
    initramfs_rootfs_dir = some/other/path
    cache_dir = some/other/path
    build_dir = some/foo
    compile_dir = some/other/foo
    destination_dir = some/dir
    sources_dir = some/sources
    image_name = Some_name
    cross_pre = some/script.sh arg1 arg2
    cross_post = some/script2.sh argA argB
    pre = some/script3.sh arg3 arg4
    post = some/script4.sh arg5 arg6
    build_image = some/build.sh arg7
    cache_vars = PATH BAR BAZ
    build_image = some/script.sh

    [cross=<target>] # cross compiler target that builds a single component
    url = http://www.kernel.org/some.tarball.tar.xz
    url = http://www.kernel.org/some.other.tarball.tar.xz
    sources = some-version/
    patch = patches/0001-add-magic.patch
    patch = patches/0002-add-evil.patch
    env = scripts/env/target_env
    env = scripts/env/target_env2
    build = scripts/build_target.sh <target>
    build = scripts/build_target_pt2.sh <target>
    pre = scripts/pre_target.sh <foo>
    post = scripts/post_target.sh <bar>

    As you can see, multiple statements for the same section
    are allowed.

    For more information about the definition of single parameters,
    please consult the online documentation (the design document) or
    just dig into the code ;-).
    """

    class MissingParametersError(Exception):
        """
        Exception raised when the .spec file contains missing parameters.
        """

        def __init__(self, params):
            """
            Object constructor.

            Args:
              params: a list of missing parameters.
            """
            super(SpecParser.MissingParametersError, self).__init__(
                "missing parameters")
            self.params = params

    def __init__(self, spec_file):
        super(SpecParser, self).__init__(spec_file, encoding="UTF-8")

        target_keys = {
            "build": self._mangle_argv0_executable,
            "cache_vars": self._mangle_cache_vars,
            "env": self._mangle_file,
            "patch": self._mangle_file,
            "post": self._mangle_argv0_executable,
            "pre": self._mangle_argv0_executable,
            "sources": self._mangle_string,
            "url": self._mangle_url,
        }

        self._SUPPORTED_KEYS = {
            "^ubuild$": {
                "build_dir": self._mangle_create_directory,
                "cache_dir": self._mangle_create_directory,
                "cache_vars": self._mangle_cache_vars,
                "compile_dir": self._mangle_create_directory,
                "cross_env": self._mangle_file,
                "cross_post": self._mangle_argv0_executable,
                "cross_pre": self._mangle_argv0_executable,
                "destination_dir": self._mangle_create_directory,
                "env": self._mangle_file,
                "image_name": self._mangle_string,
                "post": self._mangle_argv0_executable,
                "pre": self._mangle_argv0_executable,
                "rootfs_dir": self._mangle_directory,
                "initramfs_rootfs_dir": self._mangle_directory,
                "sources_dir": self._mangle_directory,
                "build_image": self._mangle_argv0_executable,
            },
            "^cross=.*": target_keys,
            "^pkg=.*": target_keys,
        }
        SpecParser._SUPPORTED_KEYS = self._SUPPORTED_KEYS

        target_vital = {
            "build": None,
            "url": None,
            "sources": 1,
        }

        self._parameters_validation = {
            "^ubuild$": {
                "build_dir": 1,
                "build_image": 1,
                "cache_dir": 1,
                "compile_dir": 1,
                "destination_dir": 1,
                "image_name": 1,
                "initramfs_rootfs_dir": 1,
                "rootfs_dir": 1,
                "sources_dir": 1,
            },
            "^cross=.*": target_vital,
            "^pkg=.*": target_vital,
        }

    def read(self):
        """
        Overrides _SpecParser.read(), adds metadata validation.

        Raises:
            SpecParser.MissingParametersError: when a parameter is missing.
        """
        super(SpecParser, self).read()
        self._validate()

    @classmethod
    def _is_executable(cls, path):
        """
        Return whether the given path has executable bits set.

        Args:
          path: a file path.

        Returns:
          True, if path is executable, False otherwise.
        """
        if not os.path.isfile(path):
            return False
        try:
            return os.stat(path).st_mode & (
                stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) != 0
        except OSError:
            return False

    @classmethod
    def _path_normalize(cls, spec_path, path):
        """
        Normalize a path string. If it's not absolute, make it so using
        spec_path parent directory.

        Args:
          spec_path: the .spec file path that is being parsed
          path: the path to normalize

        Returns:
          the normalized path.
        """
        if os.path.isabs(path):
            return path

        base_dir = os.path.dirname(spec_path)
        return os.path.abspath(
            os.path.normpath(
                os.path.join(base_dir, path)))

    @classmethod
    def _mangle_string(cls, _spec_path, _section_name, _param, value):
        """
        Mangle a simple string.
        Return None if invalid.

        Args:
          value: the parameter value to validate.

        Returns:
          the mangled string.
        """
        if value:
            return value

    @classmethod
    def _mangle_url(cls, _spec_path, _section_name, _param, value):
        """
        Mangle an ubuild url definition.
        Return None if invalid.

        Args:
          value: the parameter value to validate.

        Returns:
          the mangled URL tuple.
        """
        elems = value.split(None, 1)
        if not elems:
            return None
        if len(elems) == 1:
            return elems[0], elems[0].split("/")[-1]
        else:
            return elems[0], elems[1]

    @classmethod
    def _mangle_cache_vars(cls, _spec_path, section_name, _param, value):
        """
        Mangle a string containing space separated cache variables.

        Args:
          section_name: the .ini section name.
          value: the parameter value to validate.

        Returns:
          the mangled cache variables.
        """
        varz = value.split()
        if varz:
            return varz

    def _mangle_file(self, spec_path, section_name, param, value):
        """
        Mangle a regular file path.
        Return None if invalid.

        Args:
          spec_path: the .spec file path that is being parsed.
          section_name: the .ini section name.
          param: the parameter name inside the section.
          value: the parameter value to validate.

        Returns:
          the mangled file path.
        """
        new_value = self._path_normalize(spec_path, value)
        if not os.path.isfile(new_value):
            self._logger.error(
                "[%s] %s: not found: '%s'",
                section_name, param, value)
            return None
        return new_value

    def _mangle_directory(self, spec_path, section_name, param, value):
        """
        Mangle a directory path.
        Return None if invalid.

        Args:
          spec_path: the .spec file path that is being parsed.
          section_name: the .ini section name.
          param: the parameter name inside the section.
          value: the parameter value to validate.

        Returns:
          the mangled directory.
        """
        new_value = self._path_normalize(spec_path, value)
        if not os.path.isdir(new_value):
            self._logger.error(
                "[%s] %s: not found: '%s'",
                section_name, param, value)
            return None
        return new_value

    def _mangle_create_directory(self, spec_path, section_name, param, value):
        """
        Mangle a directory path, create it if not found.
        Return None if invalid.

        Args:
          spec_path: the .spec file path that is being parsed.
          section_name: the .ini section name.
          param: the parameter name inside the section.
          value: the parameter value to validate.

        Returns:
          the mangled (and created if not found) directory.
        """
        new_value = self._path_normalize(spec_path, value)

        try:
            os.makedirs(new_value, 0o755)
        except OSError as err:
            if err.errno != errno.EEXIST:
                self._logger.exception(
                    "[%s] %s: cannot create directory: '%s'",
                    section_name, param, new_value)
                return None
        return new_value

    def _mangle_argv0_executable(self, spec_path, section_name, param, value):
        """
        Ensure that the first element of the list points to an
        existing file and it has the executable bits set.

        Args:
          spec_path: the .spec file path that is being parsed.
          section_name: the .ini section name.
          param: the parameter name inside the section.
          value: the parameter value to validate.
        """
        args = shlex.split(value)
        if not args:
            self._logger.error(
                "[%s] %s: invalid parameter: '%s'",
                section_name, param, value)
            return None

        exe = self._path_normalize(spec_path, args[0])
        if not self._is_executable(exe):
            self._logger.error(
                "[%s] %s: not executable: '%s'",
                section_name, param, value)
            return None

        args = [exe] + args[1:]
        return args

    @classmethod
    def _validate_section(cls, match):
        """
        Reimpemented from _SpecParser.
        """
        # a new repository begins
        groups = match.groups()
        if not groups:
            return

        candidate = groups[0]
        supported = sorted(cls._SUPPORTED_KEYS.keys())
        for key in supported:
            if re.match(key, candidate):
                return candidate

        return None

    def _validate(self):
        """
        Validate the parsed metadata, raise MissingParametersError if parameters
        are missing.
        """
        missing = []

        if "ubuild" not in self.keys():
            missing.append("[ubuild] section is missing")

        for section in sorted(self.keys()):
            validation_data = None
            for section_re, param_data in self._parameters_validation.items():
                if re.match(section_re, section):
                    validation_data = param_data
                    break
            if validation_data is None:
                continue

            data = self[section]
            for param, qty in validation_data.items():
                if param not in data:
                    missing.append("[%s].%s not set" % (section, param))
                elif qty is None:
                    continue
                elif len(data[param]) > qty or len(data[param]) < qty:
                    missing.append("[%s].%s maximum %d occurrences" % (
                        section, param, qty))
        if missing:
            raise SpecParser.MissingParametersError(missing)

    def cache_vars(self):
        """
        Return the cache_vars metadata.
        """
        cache_vars = set()
        for lst in self.ubuild()["cache_vars"]:
            cache_vars.update(lst)
        return sorted(cache_vars)

    def target_cache_vars(self, target):
        """
        Return the cache_vars metadata for target, if any, or None.

        Args:
          the given build target.

        Raises:
          KeyError: if target is not found.
        """
        cache_vars = set()
        for lst in self[target].get("cache_vars", []):
            cache_vars.update(lst)
        return sorted(cache_vars)

    def ubuild(self):
        """
        Return the ubuild section metadata.
        """
        return self["ubuild"]

    def build_dir(self):
        """
        Return the build_dir metadata value.
        """
        return self.ubuild()["build_dir"][0]

    def build_image(self):
        """
        Return the build_image metadata value.
        """
        return self.ubuild()["build_image"][0]

    def cache_dir(self):
        """
        Return the cache_dir metadata value.
        """
        return self.ubuild()["cache_dir"][0]

    def compile_dir(self):
        """
        Return the compile_dir metadata value.
        """
        return self.ubuild()["compile_dir"][0]

    def destination_dir(self):
        """
        Return the destination_dir metadata value.
        """
        return self.ubuild()["destination_dir"][0]

    def image_name(self):
        """
        Return the image_name metadata value.
        """
        return self.ubuild()["image_name"][0]

    def initramfs_rootfs_dir(self):
        """
        Return the initramfs_rootfs_dir metadata value.
        """
        return self.ubuild()["initramfs_rootfs_dir"][0]

    def rootfs_dir(self):
        """
        Return the rootfs_dir metadata value.
        """
        return self.ubuild()["rootfs_dir"][0]

    def sources_dir(self):
        """
        Return the sources_dir metadata value.
        """
        return self.ubuild()["sources_dir"][0]

    def target_sources_dir(self, target):
        """
        Return the target "sources" directory value.
        """
        return self[target]["sources"][0]

    def cross_targets(self):
        """
        Return an ordered list of cross compiler targets.
        """
        return [x for x in self._ordered_sections if x.startswith("cross=")]

    def pkg_targets(self):
        """
        Return an ordered list of package targets.
        """
        return [x for x in self._ordered_sections if x.startswith("pkg=")]


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

    def __init__(self, seed, sources_dir, cache_dir, variables):
        """
        Object constructor.

        Args:
          seed: seed string to feed the cache key hash generator with.
          sources_dir: the directory in where source tarballs are downloaded.
          cache_dir: the cache directory in where all the cached
              tarballs are to be found.
          variables: the environment variables used for cache validation.
        """
        self._seed = seed
        self._sources_dir = sources_dir
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

    def _generate_entry_name(self, tarball_names, builds, patches, environment):
        """
        Given a set of input information, generate a cache entry file name.
        """
        sha = hashlib.sha1()
        sha.update(self._seed)
        sha.update("--")
        for args in builds:
            sha.update("--")
            for arg in args:
                sha.update(arg)
            sha.update("--")

        sha.update("--")
        for patch in patches:
            sha.update(self._sha1(patch))

        sha.update("--")
        for tarball in tarball_names:
            sha.update(tarball)
            path = os.path.join(self._sources_dir, tarball)
            if os.path.isfile(path):
                sha.update(self._sha1(path))
            else:
                sha.update(path) # if not found, just preserve a seat

        sha.update("--")
        for k in self._vars:
            v = environment.get(k, "")
            sha.update("%s=%s\n" % (k, v))

        sha.update("--")
        tarball_names_str = "_".join(tarball_names)
        entry_name = "%s_%s.tar.xz" % (tarball_names_str, sha.hexdigest(),)
        entry_path = os.path.abspath(os.path.join(self._dir, entry_name))
        return entry_path

    def lookup(self, tarball_names, builds, patches, environment):
        """
        Execute a cache lookup. Return a path to a tarball file.

        Args:
          tarball_names: list of names of the source tarballs.
          builds: a list of build executable arguments for the target.
          patches: list of patches to apply.
          environment: current build environment.

        Returns:
          a valid file path.
        """
        entry_path = self._generate_entry_name(
            tarball_names, builds, patches, environment)

        if os.path.isfile(entry_path):
            return entry_path

    def pack(self, image_dir, tarball_names, builds, patches, environment):
        """
        Compress the build directory into a tarball and place it
        into the cache directory.

        Args:
          image_dir: the directory in where the tarball has been built.
          tarball_names: list of names of the source tarballs.
          builds: a list of build executable arguments for the target.
          patches: list of patches to apply.
          environment: current build environment.

        Returns:
          An exit status.
        """
        entry_path = self._generate_entry_name(
            tarball_names, builds, patches, environment)

        tmp_entry_path = entry_path + ".tmp"
        args = ("tar", "-c", "-J", "-p", "-f", tmp_entry_path, "./")
        exit_st = subprocess.call(args, cwd=image_dir)
        if exit_st == 0:
            os.rename(tmp_entry_path, entry_path)
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


class Ubuild(object):
    """
    This class is responsible of building images.
    """

    cfg_file = os.getenv(
        "UBUILD_LOGGING_CFGFILE",
        os.path.join(
            os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
            "conf/ubuild.logging.conf"))
    if os.path.isfile(cfg_file):
        logging.config.fileConfig(cfg_file, disable_existing_loggers=False)
    else:
        logging.basicConfig()

    def __init__(self, spec, files):
        """
        Ubuild constructor.

        Args:
          spec: a SpecParser object.
          files: a list of file paths that have been used to generate spec.
        """
        self._logger = logging.getLogger("ubuild.Handler")
        self._spec = spec
        self._files = files
        self._spec_name = ", ".join(self._files)

    def _cacher(self, target):
        """
        Return an instance of UbuildCache if possible, otherwise None.

        Args:
          target: the build target name.
          target_cache_vars: the cache_vars metadata for the given target.
        """
        cache_dir = self._spec.cache_dir()
        if cache_dir is None:
            self._logger.warning(
                "Ubuild Cache disabled because cache_dir is unset")
            return None

        target_cache_vars = self._spec.target_cache_vars(target)
        ubuild_cache_vars = self._spec.cache_vars()
        cache_vars = sorted((set(ubuild_cache_vars) | set(target_cache_vars)))
        sources_dir = self._spec.sources_dir()
        return UbuildCache(target, sources_dir, cache_dir, cache_vars)

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
            ("UBUILD_SPEC_PATH", "path"),
            ("UBUILD_BUILD_DIR", "build_dir"),
            ("UBUILD_COMPILE_DIR", "compile_dir"),
            ("UBUILD_INITRAMFS_ROOTFS_DIR", "initramfs_rootfs_dir"),
            ("UBUILD_ROOTFS_DIR", "rootfs_dir"),
            ("UBUILD_SOURCES_DIR", "sources_dir"),
            ("UBUILD_CACHE_DIR", "cache_dir"),
            ("UBUILD_DESTINATION_DIR", "destination_dir"),
            ("UBUILD_IMAGE_NAME", "image_name"),
            )
        for env_var, env_meta in env_keys:
            value = getattr(self._spec, env_meta)()
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
        env_sourcer = os.path.abspath(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "core", "env_sourcer.sh"))
        assert os.path.isfile(env_sourcer), "%s not found" % (env_sourcer,)

        self._logger.info(
            "[%s] sourcing: %s", self._spec_name, env_file)
        args = (env_sourcer, env_file)
        tmp_fd, tmp_path = None, None

        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=self._spec.build_dir(),
                prefix="ubuild._source")

            env_dir = os.path.dirname(env_file)
            env_env = self._setup_environment({})
            exit_st = subprocess.call(
                args, stdout=tmp_fd, env=env_env, cwd=env_dir)
            if exit_st != 0:
                self._logger.error(
                    "[%s] error sourcing env file: %s, exit status: %d",
                    self._spec_name, env_file, exit_st)
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

    def _pre_post_build(self, args, env):
        """
        Execute a {cross_,}{pre,post}_build script, if any is set.

        Args:
          args: {cross_,}pre_build script arguments or None.

        Returns:
          an exit status.
        """
        if not args:
            return 0

        self._logger.info(
            "[%s] spawning: %s",
            self._spec_name,
            " ".join(args)
            )

        script_dir = os.path.dirname(args[0])
        env = self._setup_environment(env)
        exit_st = subprocess.call(args, env=env, cwd=script_dir)

        log_func = self._logger.info
        if exit_st != 0:
            log_func = self._logger.error
        log_func(
            "[%s] exit status: %d",
            self._spec_name,
            exit_st
            )
        return exit_st

    def _setup(self):
        """
        Setup build_dir and initializes other build directories.
        """
        build_dir = self._spec.build_dir()
        if os.path.isdir(build_dir):
            self._logger.info(
                "[%s] cleaning build_dir %s",
                self._spec_name, build_dir)
            try:
                dir_cont = os.listdir(build_dir)
            except OSError:
                self._logger.exception("cannot list build_dir content")
                return 1

            for sub in dir_cont:
                path = os.path.join(build_dir, sub)
                shutil.rmtree(path, True)
        return 0

    def _build(self, target, base_env, metadata):
        """
        Build a single target.

        Args:
          target: the build target name.
          metadata: the build target metadata.

        Returns:
           an exit status.
        """
        env = base_env.copy()
        env_fs = metadata.get("env", [])
        for env_f in env_fs:
            self._logger.info(
                "[%s] reading package env: %s",
                self._spec_name, env_f)
            file_env = self._env_source(env_f)
            if file_env is None:
                self._logger.error(
                    "[%s] cannot source env file: %s",
                    self._spec_name, env_f)
                return 1
            env.update(file_env)

        scripts = metadata["build"]
        urls = metadata.get("url", [])
        patches = metadata.get("patch", [])
        build_dir = self._spec.build_dir()

        self._logger.info(
            "[%s] building...", self._spec_name)
        for url, rename in urls:
            self._logger.info("  URL: %s -> %s", url, rename)
        for args in scripts:
            self._logger.info("  build script: %s", " ".join(args))
        for patch in patches:
            self._logger.info("  patch: %s", patch)

        env = self._setup_environment(env)

        patches_str = " ".join(patches)
        if patches_str:
            self._logger.debug("Setting UBUILD_PATCHES='%s'", patches_str)
            env["UBUILD_PATCHES"] = patches_str

        url_str = ";".join(["%s %s" % (x, y) for x, y in urls])
        self._logger.debug("Setting UBUILD_SRC_URI='%s'", url_str)
        env["UBUILD_SRC_URI"] = url_str

        self._logger.debug(
            "Setting UBUILD_TARGET_NAME='%s'", target)
        env["UBUILD_TARGET_NAME"] = target

        target_sources_dir = self._spec.target_sources_dir(target)
        self._logger.debug(
            "Setting UBUILD_SOURCES='%s'", target_sources_dir)
        env["UBUILD_SOURCES"] = target_sources_dir

        pre = metadata.get("pre", [])
        for args in pre:
            exit_st = self._pre_post_build(args, env)
            if exit_st != 0:
                return exit_st

        tarball_names = [x[1] for x in urls]
        cacher = self._cacher(target)
        cache_file = None
        if cacher:
            cache_file = cacher.lookup(
                tarball_names, scripts,
                patches, env)

        if cache_file:
            self._logger.info(
                "[%s] Build of %s cached to %s",
                self._spec_name, target, cache_file)
            exit_st = cacher.unpack(build_dir, cache_file)
            if exit_st != 0:
                self._logger.error(
                    "[%s] unpack of %s failed with exit status: %d",
                    self._spec_name, cache_file, exit_st)
                return exit_st

        else:

            image_dir = None
            try:
                try:
                    image_dir = tempfile.mkdtemp(
                        dir=build_dir, prefix=".ubuild_image.")
                except (OSError, IOError):
                    self._logger.exception(
                        "cannot create image_dir inside build_dir")
                    return 1

                self._logger.debug("Setting UBUILD_IMAGE_DIR=%s", image_dir)
                env["UBUILD_IMAGE_DIR"] = image_dir

                for args in scripts:
                    script = args[0]
                    script_dir = os.path.dirname(script)
                    exit_st = subprocess.call(
                        args, env=env, cwd=script_dir)

                    log_func = self._logger.info
                    if exit_st != 0:
                        log_func = self._logger.error
                    log_func("[%s] %s exit status: %d",
                             self._spec_name, script,
                             exit_st)
                    if exit_st != 0:
                        return exit_st

                if cacher:

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
                            "moved to UBUILD_IMAGE_DIR, scripts: %s",
                            self._spec_name, target,
                            ", ".join([x[0] for x in scripts]))
                        return 1

                    exit_st = cacher.pack(
                        image_dir, tarball_names, scripts, patches, env)
                    if exit_st != 0:
                        self._logger.error(
                            "[%s] pack of %s failed with exit status: %d",
                            self._spec_name, target, exit_st)
                        # ignore failure.

            finally:
                if image_dir is not None:
                    shutil.rmtree(image_dir, True)

        post = metadata.get("post", [])
        for args in post:
            exit_st = self._pre_post_build(args, env)
            if exit_st != 0:
                return exit_st

        self._logger.info("")

        return 0

    def build(self):
        """
        Build an image using the provided build information.

        Args:
          parser: a SpecParser object containing instructions on what to build.

        Return:
          an exit status.
        """
        exit_st = self._setup()
        if exit_st != 0:
            return exit_st

        metadata = self._spec.ubuild()
        base_env = os.environ.copy()

        env_fs = metadata.get("cross_env", [])
        cross_env = base_env
        for env_f in env_fs:
            self._logger.info(
                "[%s] reading cross_env: %s",
                self._spec_name, env_f)
            file_env = self._env_source(env_f)
            if file_env is None:
                self._logger.error(
                    "[%s] cannot source env file: %s",
                    self._spec_name, env_f)
                return 1
            cross_env.update(file_env)

        cross_pre = metadata.get("cross_pre", [])
        for args in cross_pre:
            exit_st = self._pre_post_build(args, cross_env)
            if exit_st != 0:
                return exit_st

        cross_targets = self._spec.cross_targets()
        for target in cross_targets:
            data = self._spec[target]
            exit_st = self._build(target, cross_env, data)
            if exit_st != 0:
                return exit_st

        cross_post = metadata.get("cross_post", [])
        for args in cross_post:
            exit_st = self._pre_post_build(args, cross_env)
            if exit_st != 0:
                return exit_st

        env_fs = metadata.get("env", [])
        env = base_env
        for env_f in env_fs:
            self._logger.info(
                "[%s] reading env: %s",
                self._spec_name, env_f)
            file_env = self._env_source(env_f)
            if file_env is None:
                self._logger.error(
                    "[%s] cannot source env file: %s",
                    self._spec_name, env_f)
                return 1
            env.update(file_env)

        pre = metadata.get("pre", [])
        for args in pre:
            exit_st = self._pre_post_build(args, env)
            if exit_st != 0:
                return exit_st

        pkg_targets = self._spec.pkg_targets()
        for target in pkg_targets:
            data = self._spec[target]
            exit_st = self._build(target, env, data)
            if exit_st != 0:
                return exit_st

        post = metadata.get("post", [])
        for args in post:
            exit_st = self._pre_post_build(args, env)
            if exit_st != 0:
                return exit_st

        build_env = self._setup_environment(base_env)
        args = self._spec.build_image()
        if args:
            exit_st = self._pre_post_build(args, build_env)
            if exit_st != 0:
                return exit_st

        return 0


def main(argv):
    """
    The main Ubuild main() ;-)

    Args:
      argv: a full and bloated *argv[]

    Returns:
      an exit status.
    """
    parser = argparse.ArgumentParser(
        description="Automated Embedded System Images Builder")

    parser.add_argument(
        "spec", nargs="+", metavar="<spec>", type=file,
        help="ubuild spec file")

    try:
        nsargs = parser.parse_args(argv[1:])
    except IOError as err:
        if err.errno == errno.ENOENT:
            sys.stderr.write("%s: %s\n" % (err.strerror, err.filename))
            return 1
        raise

    specs = []
    exit_st = 0
    for spec_f in nsargs.spec:
        parser = SpecParser(spec_f.name)
        try:
            parser.read()
        except SpecParser.MissingParametersError as err:
            sys.stderr.write("Missing parameters in %s:\n" % (spec_f.name,))
            for param in err.params:
                sys.stderr.write(" - %s\n" % (param,))
            exit_st = 2
            continue
        except SpecPreprocessor.PreprocessorError as err:
            sys.stderr.write("Preprocessor error %s in %s\n" % (
                spec_f.name, err))
            exit_st = 2
            continue
        specs.append((parser, [spec_f.name]))

    if exit_st != 0:
        return exit_st

    for spec, files in specs:
        try:
            exit_st = Ubuild(spec, files).build()
        except KeyboardInterrupt:
            return 1
        if exit_st != 0:
            return exit_st

    return 0

if __name__ == "__main__":
    sys.argv[0] = "ubuild"
    raise SystemExit(main(sys.argv))
