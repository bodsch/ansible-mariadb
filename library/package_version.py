#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import re

from ansible.module_utils import distro
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}


class PackageVersion(object):
    """
        Main Class
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.package_version = module.params.get("version")
        self.package_name = module.params.get("name")
        self.repository = module.params.get("repository")

        (self.distribution, self.version, self.codename) = distro.linux_distribution(full_distribution_name=False)

    def run(self):
        result = dict(
            failed=False,
            available_version="none"
        )

        version = ''
        error = True
        msg = "not supported distribution: {}".format(self.distribution)

        self.module.log(msg="  distribution : '{}'".format(self.distribution))

        if self.distribution.lower() in ["debian", "ubuntu"]:
            error, version, msg = self._search_apt()

        if self.distribution.lower() in ["centos", "oracle", "redhat", "fedora"]:
            error, version, msg = self._search_yum()

        if self.distribution.lower() in ["arch"]:
            error, version, msg = self._search_pacman()

        # self.module.log(msg="  error   : '{}'".format(error))
        self.module.log(msg="  version : '{}'".format(version))
        # self.module.log(msg="  msg     : '{}'".format(msg))

        if error:
            return dict(
                failed=True,
                available_versions=version,
                msg=msg
            )

        major_version, minor_version, _ = version.split(".")

        version = dict(
            full_version=version,
            platform_version='.'.join([major_version, minor_version]),
            major_version=major_version
        )

        result = dict(
            failed=error,
            available=version,
            msg=msg
        )

        return result

    def _search_apt(self):
        """
            apt-cache show php | grep Version | sort | tail -n1 | awk -F'[:+]' '{print $3}' | tr -d '[:space:]'

            bionic provides PHP 7.2
            buster provides PHP 7.3
            stretch provides PHP 7.0
        """
        import apt

        version = ''

        cache = apt.cache.Cache()
        cache.update()
        cache.open()

        pkg = cache[self.package_name]

        if(pkg):
            # self.module.log(msg="  - pkg       : {} ({})".format(pkg, type(pkg)))
            # self.module.log(msg="  - installed : {}".format(pkg.is_installed))
            # self.module.log(msg="  - shortname : {}".format(pkg.shortname))
            # self.module.log(msg="  - versions  : {}".format(pkg.versions))
            # self.module.log(msg="  - versions  : {}".format(pkg.versions[0]))

            pkg_version = pkg.versions[0]
            version = pkg_version.version

            pattern = re.compile(r"(.*?)(?=\-)")

            # debian:9 : 1:10.4.20+maria~stretch'
            # debian 10: 1:10.4.20+maria~buster
            # self.module.log(msg="  - version   : '{}'".format(version))

            if version.startswith("1:"):
                pattern = re.compile(r"(?<=\:)(.*?)(?=[-+])")
                # pattern = re.compile(r"(?<=\:)(.*?)(?=\-)")

            result = re.search(pattern, version)

            if result:
                version = result.group(1)

        return False, version, ''

    def _search_yum(self):
        """
            yum info $package | grep Summary | cut -d ':' -f 2 | tr -d '[:space:]' | cut -c23-25

            dnf info mariadb | grep Version | cut -d ':' -f 2 | tr -d '[:space:]'
        """
        pattern = re.compile(r".*Version.*: (?P<version>.*)", re.MULTILINE)

        package_version = self.package_version

        if(package_version):
            package_version = package_version.replace('.', '')

        package_mgr = self.module.get_bin_path('dnf', True)

        if(not package_mgr):
            package_mgr = self.module.get_bin_path('yum', False)

        if(not package_mgr):
            return True, "", "no valid package manager (yum or dnf) found"

        # self.module.log(msg="  package manager: '{0}'".format(package_mgr))

        args = [package_mgr]
        args.append("info")
        args.append(self.package_name)
        args.append("--disablerepo")
        args.append("*")
        args.append("--enablerepo")
        args.append(self.repository)

        self.module.log(msg="  package manager: '{0}'".format(args))

        rc, out, err = self.module.run_command(
            args,
            check_rc=False)

        version = ''

        if(rc == 0):
            versions = []

            for line in out.splitlines():
                # self.module.log(msg="line     : {}".format(line))
                for match in re.finditer(pattern, line):
                    result = re.search(pattern, line)
                    versions.append(result.group('version'))

            self.module.log(msg="versions      : '{0}'".format(versions))

            if(len(versions) == 0):
                msg = 'nothing found'
                error = True

            if(len(versions) == 1):
                msg = ''
                error = False
                version = versions[0]

            if(len(versions) > 1):
                msg = 'more then one result found! choose one of them!'
                error = True
                version = ', '.join(versions)
        else:
            msg = 'nothing found'
            error = True

        return error, version, msg

    def _search_pacman(self):
        """
        """
        self.module.log(msg="= {function_name}()".format(function_name="_search_pacman"))

        pattern = re.compile(r"^extra/{} (?P<version>.*)-\d".format(self.package_name), re.MULTILINE)

        pacman_bin = self.module.get_bin_path('pacman', True)
        args = [pacman_bin]
        args.append("--noconfirm")
        args.append("--sync")
        args.append("--search")
        args.append(self.package_name)

        rc, out, err = self._pacman(args)

        version = re.search(pattern, out)

        if version:
            return False, version.group('version'), ""
        else:
            return True, "", "not found"

    def _pacman(self, cmd):
        """
        """
        self.module.log(msg="cmd: {}".format(cmd))

        rc, out, err = self.module.run_command(cmd, check_rc=True)
        # self.module.log(msg="  rc : '{}'".format(rc))
        # self.module.log(msg="  out: '{}' ({})".format(out, type(out)))
        # self.module.log(msg="  err: '{}'".format(err))
        return rc, out, err

# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            version=dict(required=False, default=''),
            name=dict(required=True),
            repository=dict(required=False, default="MariaDB")
        ),
        supports_check_mode=False,
    )

    helper = PackageVersion(module)
    result = helper.run()

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
