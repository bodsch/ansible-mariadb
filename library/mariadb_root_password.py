#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import hashlib

from ansible.module_utils.basic import AnsibleModule

try:
    from configparser import ConfigParser, DuplicateSectionError
    # from configparser import NoSectionError, NoOptionError
except ImportError:
    # ver. < 3.0
    from ConfigParser import ConfigParser, DuplicateSectionError
    # from ConfigParser import NoSectionError, NoOptionError


DOCUMENTATION = """
---
module: mariadb_root_password.py
author:
    - 'Bodo Schulz'
short_description: set or change the root password and write the /root/.my.cnf file
description: ''
"""

EXAMPLES = """
- name: set root password
  mariadb_root_password:
    dba_root_username: "{{ mariadb_root_username }}"
    dba_root_password: "{{ mariadb_root_password }}"
    dba_socket: "{{ mariadb_socket }}"
    dba_config_directory: "{{ mariadb_config_dir }}"
    mycnf_file: "{{ mariadb_root_home }}/.my.cnf"

"""

# ---------------------------------------------------------------------------------------


class MariaDBRootPassword(object):
    """
      Main Class to implement the Icinga2 API Client
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module

        self.dba_root_username = module.params.get("dba_root_username")
        self.dba_root_password = module.params.get("dba_root_password")
        self.dba_socket = module.params.get("dba_socket")
        self.dba_hostname = module.params.get("dba_hostname")
        self.dba_config_directory = module.params.get("dba_config_directory")
        self.mycnf_file = module.params.get("mycnf_file")

        self.checksum_file = os.path.join(self.dba_config_directory, ".rootpw_configured")

        # self.module.log(msg="-------------------------------------------------------------")
        # self.module.log(msg="username      : {}".format(self.dba_root_username))
        # self.module.log(msg="password      : {}".format(self.dba_root_password))
        # self.module.log(msg="socket        : {}".format(self.dba_socket))
        # self.module.log(msg="hostname      : {}".format(self.dba_hostname))
        # self.module.log(msg="config dir    : {}".format(self.dba_config_directory))
        # self.module.log(msg="checksum file : {}".format(self.checksum_file))
        # self.module.log(msg="mycnf_file    : {}".format(self.mycnf_file))
        # self.module.log(msg="------------------------------")

        # self.db_connect_timeout = 30

    def run(self):
        """
          runner
        """
        checksum_file_exists = os.path.exists(self.checksum_file)

        old_checksum = ""
        new_checksum = ""

        self._write_mycnf()

        if checksum_file_exists:
            """
            """
            with open(self.checksum_file) as f:
                old_checksum = f.readline()

            # self.module.log(msg="  hash         : {}".format(old_checksum))

        new_checksum = self._checksum(self.dba_root_password)

        # self.module.log(msg="  hash         : {}".format(new_checksum))

        if old_checksum == new_checksum:
            return dict(
                changed=False,
                msg="password was not changed"
            )

        mysqladmin_binary = self.module.get_bin_path("mysqladmin", False)

        args = [mysqladmin_binary]
        args.append("--user")
        args.append("root")
        args.append("password")
        args.append(self.dba_root_password)

        rc, out, err = self._exec(args)

        if rc != 0:
            return dict(
                failed=True,
                msg="{} / {}".format(out, err)
            )

        """
          persist checksum
        """
        with open(self.checksum_file, "w") as checksum_file:
            checksum_file.write(new_checksum)

        return dict(
            changed=True,
            msg="password was successful set"
        )

    def _write_mycnf(self):
        """
        """
        # ini_password = None
        # ini_username = None
        # ini_socket = None
        # ini_hostname = None

        if ConfigParser:
            """
              write ini style my.cnf
            """
            config = ConfigParser()

            try:
                config.read(self.mycnf_file)
            except Exception:
                # self.module.log(msg=" ERROR : {}".format(str(e)))
                return

            # try:
            #     ini_username = config.get('client', 'user')
            # except NoOptionError:
            #     # self.module.log(msg=" WARNING : {}".format(e))
            #     pass
            #
            # try:
            #     ini_password = config.get('client', 'password')
            # except NoOptionError:
            #     # self.module.log(msg=" WARNING : {}".format(e))
            #     pass
            #
            # try:
            #     ini_socket = config.get('client', 'socket')
            # except NoOptionError:
            #     # self.module.log(msg=" WARNING : {}".format(e))
            #     pass
            #
            # try:
            #     ini_hostname = config.get('client', 'host')
            # except NoOptionError:
            #     # self.module.log(msg=" WARNING : {}".format(e))
            #     pass

            # self.module.log(msg="  - username: {}".format(ini_username))
            # self.module.log(msg="  - password: {}".format(ini_password))
            # self.module.log(msg="  - socket  : {}".format(ini_socket))
            # self.module.log(msg="  - hostname: {}".format(ini_hostname))

            try:
                config.add_section('client')
            except DuplicateSectionError:
                # self.module.log(msg=" WARNING : {}".format(e))
                pass

            config.set('client', 'user', self.dba_root_username)
            config.set('client', 'password', self.dba_root_password)

            if self.dba_socket:
                config.set('client', 'socket', self.dba_socket)

            if self.dba_hostname:
                config.set('client', 'host', self.dba_hostname)

            with open(self.mycnf_file, 'w') as configfile:    # save
                config.write(configfile)

    def _exec(self, command):
        """
          execute commands
        """
        # self.module.log(msg="command: {}".format(command))

        rc, out, err = self.module.run_command(command, check_rc=True)
        # self.module.log(msg="  rc : '{}'".format(rc))
        # self.module.log(msg="  out: '{}'".format(out))
        # self.module.log(msg="  err: '{}'".format(err))
        return rc, out, err

    def _checksum(self, plaintext):
        """
        """
        password_bytes = plaintext.encode('utf-8')
        password_hash = hashlib.sha256(password_bytes)
        return password_hash.hexdigest()


# ---------------------------------------------------------------------------------------
# Module execution.
#

def main():
    ''' ... '''
    module = AnsibleModule(
        argument_spec=dict(
            dba_root_username=dict(required=True, type='str'),
            dba_root_password=dict(required=True, type='str', no_log=True),
            dba_socket=dict(required=True, type='str'),
            dba_hostname=dict(required=False, type='str'),
            dba_config_directory=dict(required=True, type='path'),
            mycnf_file=dict(required=False, type="str", default="/root/.my.cnf"),
        ),
        supports_check_mode=False,
    )

    # module.log(msg="-------------------------------------------------------------")

    client = MariaDBRootPassword(module)
    result = client.run()

    module.log(msg="= result: {}".format(result))
    # module.log(msg="-------------------------------------------------------------")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
