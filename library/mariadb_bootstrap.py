#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2020-2024, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, print_function
import os
import grp
import pwd

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}


class MariadbBootstrap(object):
    """
        Main Class
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.mariadb_datadir = module.params.get("datadir")
        self.mariadb_basedir = module.params.get("basedir")
        self.mariadb_user = module.params.get("user")
        self.mariadb_force = module.params.get("force")
        self.mariadb_no_defaults = module.params.get("no_defaults")
        self.mariadb_skip_auth_anonymous_user = module.params.get("skip_auth_anonymous_user")
        self.mariadb_skip_name_resolve = module.params.get("skip_name_resolve")
        self.mariadb_skip_test_db = module.params.get("skip_test_db")

        self.bootstrapped_file = "/etc/.mariadb.bootstrapped"

    def get_file_ownership(self, filename):
        return (
            pwd.getpwuid(os.stat(filename).st_uid).pw_name,
            grp.getgrgid(os.stat(filename).st_gid).gr_name
        )

    def touch(self, fname):
        try:
            os.utime(fname, None)
        except OSError:
            open(fname, 'a').close()

    def run(self):
        result = dict(
            failed=False,
            msg="none"
        )

        # change into basedir (needful at archlinux)
        os.chdir("/usr")

        mariadb_install_db = self.module.get_bin_path('mysql_install_db', True)

        # no binary found
        if not mariadb_install_db:
            return dict(
                failed=True,
                msg="can't find 'mysql_install_db' on system. please install package first."
            )

        user_table_exists = os.path.exists(os.path.join(self.mariadb_datadir, "mysql", "user.frm"))
        bootstrap_file_exists = os.path.exists(self.bootstrapped_file)

        # self.module.log(msg="= user.MYD             : {}".format(os.path.join(self.mariadb_datadir, "mysql", "user.frm")))
        # self.module.log(msg="= user_table_exists    : {}".format(user_table_exists))
        # self.module.log(msg="= bootstrap_file_exists: {}".format(bootstrap_file_exists))

        # bootstrapped_file found
        if user_table_exists and bootstrap_file_exists:
            return dict(
                failed=False,
                changed=False,
                msg="mariadb is already bootstrapped"
            )

        args = []

        if self.mariadb_no_defaults:
            # Don't read default options from any option file.
            # Must be given as the first option.
            args.append("--no-defaults")

        # The login user name to use for running mysqld.
        args.append("--user")
        args.append(self.mariadb_user)

        # if self.mariadb_basedir:
        #     # The path to the MariaDB installation directory.
        #     args.append("--basedir")
        #     args.append(self.mariadb_basedir)

        # The path to the MariaDB data directory.
        args.append("--datadir")
        args.append(self.mariadb_datadir)

        args.append("--auth-root-authentication-method=socket")

        if self.mariadb_skip_auth_anonymous_user:
            # Do not create the anonymous user.
            args.append("--skip-auth-anonymous-user")

        if self.mariadb_skip_name_resolve:
            # Uses IP addresses rather than host names when creating grant table entries.
            # This option can be useful if your DNS does not work.
            args.append("--skip-name-resolve")

        # works NOT with mariadb 10.1
        if self.mariadb_skip_test_db:
            # Don't install the test database.
            args.append("--skip-test-db")

        # self.module.log(msg="  args: {}".format(args))

        rc, out, err = self.module.run_command(
            [mariadb_install_db] + args,
            check_rc=False)

        # self.module.log(msg="  rc : '{}'".format(rc))
        # self.module.log(msg="  out: '{}' ({})".format(out, type(out)))
        # self.module.log(msg="  err: '{}'".format(err))

        if rc == 0:
            self.touch(self.bootstrapped_file)

            return dict(
                failed=False,
                changed=True,
                msg="The MariaDB data directories and the system tables were successfully created."
            )
        else:
            return dict(
                failed=True,
                msg=out
            )

        return result


def main():
    """
    """
    specs = dict(
        datadir=dict(
            required=False,
            type='path',
            default='/var/lib/mysql'
        ),
        basedir=dict(
            required=False,
            type='path',
            default='/usr'
        ),
        user=dict(
            required=False,
            type='str',
            default='mysql'
        ),
        force=dict(
            required=False,
            type='bool'
        ),
        no_defaults=dict(
            required=False,
            type='bool'
        ),
        skip_auth_anonymous_user=dict(
            required=False,
            type='bool'
        ),
        skip_name_resolve=dict(
            required=False,
            type='bool'
        ),
        skip_test_db=dict(
            required=False,
            type='bool'
        ),
    )

    module = AnsibleModule(
        argument_spec=specs,
        supports_check_mode=False,
    )

    helper = MariadbBootstrap(module)
    result = helper.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
