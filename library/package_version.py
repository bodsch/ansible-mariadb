#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020-2022, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import print_function
import re

from ansible.module_utils import distro
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: package_version.py
author:
    - 'Bodo Schulz'
short_description: Attempts to determine the version of a package to be installed or already installed.
description: 'Attempts to determine the version of a package to be installed or already installed.

Supports apt, pacman, dnf (or yum) as package manager.'
"""

EXAMPLES = """
- name: get version of available package
  package_version:
    package_name: nano
  register: package_version

- name: get version of available mariadb-server
  package_version:
    state: available
    package_name: mariadb-server
  register: package_version

- name: get version of installed php-fpm
  package_version:
    package_name: php-fpm
    state: installed
  register: package_version
"""


class PackageVersion(object):
    """
    """

    def __init__(self, module):

        self.module = module

        self.state = module.params.get("state")
        self.package_name = module.params.get("package_name")
        self.package_version = module.params.get("package_version")
        self.repository = module.params.get("repository")

        (self.distribution, self.version, self.codename) = distro.linux_distribution(
            full_distribution_name=False
        )

    def run(self):
        """
        """
        version = ''
        error = True
        msg = f"unknown or unsupported distribution: '{self.distribution}'"

        if self.distribution.lower() in ["debian", "ubuntu"]:
            error, version, msg = self._search_apt()

        if self.distribution.lower() in ["arch", "artix"]:
            error, version, msg = self._search_pacman()

        if self.distribution.lower() in ["centos", "oracle", "redhat", "fedora", "rocky", "almalinux"]:
            error, version, msg = self._search_yum()

        if error:
            return dict(
                failed=True,
                available_versions=version,
                msg=msg
            )

        if version is not None:
            version_splitted = version.split(".")

            major_version = version_splitted[0]
            minor_version = version_splitted[1]

            version = dict(
                full_version=version,
                platform_version='.'.join([major_version, minor_version]),
                major_version=major_version,
                version_string_compressed=version.replace('.', '')
            )

        result = dict(
            failed=error,
            available=version,
            msg=msg
        )

        return result

    def _search_apt(self):
        """
          support apt
        """
        import apt

        cache = apt.cache.Cache()

        # try:
        #     cache.update()
        # except SystemError as error:
        #     self.module.log(msg=f"error         : {error}")
        #     raise FetchFailedException(error)
        # if not res and raise_on_error:
        #     self.module.log(msg="FetchFailedException()")
        #     raise FetchFailedException()
        # else:
        #     cache.open()

        cache.update()
        cache.open()

        try:
            pkg = cache[self.package_name]
            version_string = None

            # debian:10 / buster:
            #  [php-fpm=2:7.3+69]
            # ubuntu:20.04 / focal
            #  [php-fpm=2:7.4+75]
            # debian:9 : 1:10.4.20+maria~stretch'
            # debian 10: 1:10.4.20+maria~buster

            if pkg:
                # self.module.log(msg="  - pkg       : {} ({})".format(pkg, type(pkg)))
                # self.module.log(msg="  - installed : {}".format(pkg.is_installed))
                # self.module.log(msg="  - shortname : {}".format(pkg.shortname))
                # self.module.log(msg="  - versions  : {}".format(pkg.versions))
                # self.module.log(msg="  - versions  : {}".format(pkg.versions[0]))

                pkg_version = pkg.versions[0]
                version = pkg_version.version

                if version[1] == ":":
                    pattern = re.compile(r"(?<=\:)(?P<version>.*?)(?=[-+])")
                else:
                    pattern = re.compile(r"(?P<version>.*?)(?=[-+])")

                result = re.search(pattern, version)
                version_string = result.group('version')

        except KeyError as error:
            self.module.log(msg=f"error         : {error}")
            return False, None, f"package {self.package_name} is not installed"

        return False, version_string, ""

    def _search_yum(self):
        """
          support dnf and - as fallback - yum
        """
        package_mgr = self.module.get_bin_path('dnf', False)

        if(not package_mgr):
            package_mgr = self.module.get_bin_path('yum', True)

        if(not package_mgr):
            return True, "", "no valid package manager (yum or dnf) found"

        package_version = self.package_version

        if(package_version):
            package_version = package_version.replace('.', '')

        args = []
        args.append(package_mgr)

        args.append("info")
        args.append(self.package_name)

        if self.repository:
            args.append("--disablerepo")
            args.append("*")
            args.append("--enablerepo")
            args.append(self.repository)

        rc, out, err = self.module.run_command(
            args,
            check_rc=False)

        version = ''

        if rc == 0:
            versions = []

            pattern = re.compile(r".*Version.*: (?P<version>.*)", re.MULTILINE)
            # pattern = re.compile(
            #     r"^{0}[0-9+].*\.x86_64.*(?P<version>[0-9]+\.[0-9]+)\..*@(?P<repo>.*)".format(self.package_name),
            #     re.MULTILINE
            # )

            for line in out.splitlines():
                self.module.log(msg=f"  line     : {line}")
                for match in re.finditer(pattern, line):
                    result = re.search(pattern, line)
                    versions.append(result.group('version'))

            self.module.log(msg=f"versions      : '{versions}'")

            if len(versions) == 0:
                msg = 'nothing found'
                error = True

            if len(versions) == 1:
                msg = ''
                error = False
                version = versions[0]

            if len(versions) > 1:
                msg = 'more then one result found! choose one of them!'
                error = True
                version = ', '.join(versions)
        else:
            msg = f"package {self.package_name} not found"
            error = False
            version = None

        return error, version, msg

    def _search_pacman(self):
        """
            pacman support
            pacman --noconfirm --sync --search php7 | grep -E "^(extra|world)\\/php7 (.*)\\[installed\\]" | cut -d' ' -f2
        """
        pacman_bin = self.module.get_bin_path('pacman', True)

        version = None
        args = []
        args.append(pacman_bin)

        if self.state == "installed":
            args.append("--query")
        else:
            args.append("--noconfirm")
            args.append("--sync")

        args.append("--search")
        args.append(self.package_name)

        rc, out, err = self._pacman(args)

        if rc == 0:
            pattern = re.compile(
                r'^(?P<repository>core|extra|community|world|local)\/{}[0-9\s]*(?P<version>\d\.\d).*-.*'.format(self.package_name),
                re.MULTILINE
            )

            result = re.search(pattern, out)

            msg = ''
            error = False
            version = result.group('version')

        else:
            msg = f"package {self.package_name} not found"
            error = False
            version = None

        return error, version, msg

    def _pacman(self, cmd):
        """
          support pacman
        """
        # self.module.log(msg="cmd: {}".format(cmd))

        rc, out, err = self.module.run_command(cmd, check_rc=False)
        # self.module.log(msg="  rc : '{}'".format(rc))
        # self.module.log(msg="  out: '{}' ({})".format(out, type(out)))
        # self.module.log(msg="  err: '{}'".format(err))
        return rc, out, err

# ---------------------------------------------------------------------------------------
# Module execution.
#


def main():
    ''' ... '''
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                choices=[
                    "installed",
                    "available",
                ],
                default="available"
            ),
            package_name=dict(
                required=True,
                type='str'
            ),
            package_version=dict(
                required=False,
                default=''
            ),
            repository=dict(
                required=False,
                default=""
            )
        ),
        supports_check_mode=False,
    )

    result = PackageVersion(module).run()

    module.log(msg="= result : '{0}'".format(result))

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
