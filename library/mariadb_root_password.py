#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2020-2024, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import os
import hashlib

from ansible.module_utils.basic import AnsibleModule

try:
    from configparser import ConfigParser, DuplicateSectionError
    from configparser import NoSectionError, NoOptionError
except ImportError:
    # ver. < 3.0
    from ConfigParser import ConfigParser, DuplicateSectionError
    from ConfigParser import NoSectionError, NoOptionError


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
    dba_bind_address: "{{ mariadb_bind_address | default(omit) }}
    dba_socket: "{{ mariadb_socket | default(omit) }}"
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
        self.dba_bind_address = module.params.get("dba_bind_address")  # TODO: rename to bind_address
        self.dba_config_directory = module.params.get("dba_config_directory")
        self.mycnf_file = module.params.get("mycnf_file")

        self.checksum_file = os.path.join(self.dba_config_directory, ".rootpw_configured")

        # self.module.log(msg="-------------------------------------------------------------")
        # self.module.log(msg=f"username      : {self.dba_root_username}")
        # self.module.log(msg=f"password      : {self.dba_root_password}")
        # self.module.log(msg=f"socket        : {self.dba_socket}")
        # self.module.log(msg=f"bind_address  : {self.dba_bind_address}")
        # self.module.log(msg=f"config dir    : {self.dba_config_directory}")
        # self.module.log(msg=f"checksum file : {self.checksum_file}")
        # self.module.log(msg=f"mycnf_file    : {self.mycnf_file}")
        # self.module.log(msg="------------------------------")

        # self.db_connect_timeout = 30

    def run(self):
        """
          runner
        """
        checksum_file_exists = os.path.exists(self.checksum_file)

        old_checksum = ""
        new_checksum = ""

        if checksum_file_exists:
            """
            """
            with open(self.checksum_file) as f:
                old_checksum = f.readline()

        new_checksum = self._checksum(self.dba_root_password)

        if old_checksum == new_checksum:
            return dict(
                changed=False,
                msg="password was not changed"
            )

        self._write_mycnf()

        mysqladmin_binary = self.module.get_bin_path("mysqladmin", False)

        args = [mysqladmin_binary]
        args.append("--user")
        args.append("root")

        if self.dba_bind_address:
            args.append("--host")
            args.append(self.dba_bind_address)

        if self.dba_root_password:
            args.append("password")
            args.append(self.dba_root_password)

        self.module.log(msg=f" - args: {args}")

        rc, out, err = self._exec(command=args, check_rc=False)

        if rc != 0:
            return dict(
                failed=True,
                msg=f"{out} / {err}"
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
        ini_password = None
        ini_username = None
        ini_socket = None
        ini_hostname = None

        if ConfigParser:
            """
              write ini style my.cnf
            """
            config = ConfigParser()

            try:
                config.read(self.mycnf_file)
            except Exception as e:
                self.module.log(msg=f" ERROR : {e}")
                return

            try:
                ini_username = config.get('client', 'user')

                try:
                    ini_password = config.get('client', 'password')
                except NoOptionError:
                    # self.module.log(msg=" WARNING : {}".format(e))
                    pass

                try:
                    ini_socket = config.get('client', 'socket')
                except NoOptionError:
                    # self.module.log(msg=" WARNING : {}".format(e))
                    pass

                try:
                    ini_hostname = config.get('client', 'host')
                except NoOptionError:
                    # self.module.log(msg=" WARNING : {}".format(e))
                    pass

            except NoSectionError:
                # self.module.log(msg=" WARNING : {}".format(e))
                pass

            # self.module.log(msg=f"  - username: {ini_username}")
            # self.module.log(msg=f"  - password: {ini_password}")
            # self.module.log(msg=f"  - socket  : {ini_socket}")
            # self.module.log(msg=f"  - hostname: {ini_hostname}")

            try:
                config.add_section('client')
            except DuplicateSectionError:
                # self.module.log(msg=" WARNING : {}".format(e))
                pass

            config.set('client', 'user', self.dba_root_username)
            config.set('client', 'password', self.dba_root_password)

            if self.dba_socket:
                config.set('client', 'socket', self.dba_socket)

            if self.dba_bind_address:
                config.set('client', 'host', self.dba_bind_address)

            # config_content = {section: dict(config[section]) for section in config.sections()}
            # self.module.log(msg=f" config: {config_content}")

            with open(self.mycnf_file, 'w') as configfile:
                config.write(configfile)

    def _exec(self, command, check_rc=True):
        """
          execute commands
        """
        rc, out, err = self.module.run_command(command, check_rc=check_rc)
        self.module.log(msg=f"  rc : '{rc}'")

        if rc != 0:
            self.module.log(msg=f"  out: '{out}'")
            self.module.log(msg=f"  err: '{err}'")

        return rc, out, err

    def _checksum(self, plaintext):
        """
        """
        password_bytes = plaintext.encode('utf-8')
        password_hash = hashlib.sha256(password_bytes)
        return password_hash.hexdigest()


def main():
    """
    """
    specs = dict(
        dba_root_username=dict(
            required=True,
            type='str'
        ),
        dba_root_password=dict(
            required=True, type='str',
            no_log=True
        ),
        dba_socket=dict(
            required=True,
            type='str'
        ),
        dba_bind_address=dict(
            required=False,
            type='str'
        ),
        dba_config_directory=dict(
            required=True,
            type='path'
        ),
        mycnf_file=dict(
            required=False,
            type="str",
            default="/root/.my.cnf"
        ),
    )

    module = AnsibleModule(
        argument_spec=specs,
        supports_check_mode=False,
    )

    client = MariaDBRootPassword(module)
    result = client.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
