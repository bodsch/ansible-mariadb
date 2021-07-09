#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.mysql import mysql_driver, mysql_driver_fail_msg

# try:
#     import pymysql as mysql_driver
# except ImportError:
#     try:
#         import MySQLdb as mysql_driver
#     except ImportError:
#         mysql_driver = None
#
# mysql_driver_fail_msg = 'The PyMySQL (Python 2.7 and Python 3.X) or MySQL-python (Python 2.X) module is required.'

DOCUMENTATION = """
---
module: mysql_schema.py
author:
    - 'Bodo Schulz'
short_description: check it the named schema exists in a mysql.
description: ''
"""

EXAMPLES = """
- name: ensure, table_schema is present
  icinga2_ido_version:
    dba_host: ::1
    dba_user: root
    dba_password: password
"""

# ---------------------------------------------------------------------------------------


class MariaDBSecure(object):
    """
      Main Class to implement the Icinga2 API Client
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module

        self.disallow_anonymous_users = module.params.get("disallow_anonymous_users")
        self.disallow_test_database = module.params.get("disallow_test_database")
        self.disallow_remote_root_login = module.params.get("disallow_remote_root_login")
        self.dba_root_username = module.params.get("dba_root_username")
        self.dba_root_password = module.params.get("dba_root_password")
        self.mycnf_file = module.params.get("mycnf_file")

        self.db_connect_timeout = 30

    def run(self):
        """
          runner
        """
        # mysqladmin_binary = self.module.get_bin_path("mysqladmin", False)
        # mysql_binary = self.module.get_bin_path("mysql", False)
        #
        # args = [mysqladmin_binary]
        # args.append("--user")
        # args.append("root")
        # args.append("status")
        #
        # rc, out, err = self._exec(args)

        if self.disallow_remote_root_login:
            state, error, error_message = self._remove_anonymous_users()

            self.module.log(msg=" - disallow remote root login: {}".format(state))

            if error:
                return dict(
                    failed=True,
                    msg=error_message
                )

        if self.disallow_anonymous_users:
            state, error, error_message = self._remove_remote_root_login()

            self.module.log(msg=" - disallow anonymous users: {}".format(state))

            if error:
                return dict(
                    failed=True,
                    msg=error_message
                )

        if self.disallow_test_database:
            state, error, error_message = self._remove_test_database()

            self.module.log(msg=" - remove test database: {}".format(state))

            if error:
                return dict(
                    failed=True,
                    msg=error_message
                )

        res = dict(
            changed=False,
            msg="all fine.",
        )

        return res

    def _remove_anonymous_users(self):
        """
        """
        cursor, conn, error, message = self._mysql_connect()

        if error:
            return (False, error, message)

        query = "delete from mysql.user where user = '{0}' and host not in ('localhost', '127.0.0.1', '::1')"
        query = query.format(self.dba_root_username)

        # self.module.log(msg="  query : '{}'".format(query))

        try:
            cursor.execute(query)
            cursor.fetchone()
            cursor.close()

        except Exception as e:
            conn.rollback()
            self.module.fail_json(msg="Cannot execute SQL '%s' : %s" % (query, to_native(e)))

        return (True, False, None)

    def _remove_remote_root_login(self):
        """
        """
        results = None

        cursor, conn, error, message = self._mysql_connect()

        if error:
            return (False, error, message)

        query = "select host, user, password from mysql.user where user = ''"

        # self.module.log(msg="  query : '{}'".format(query))

        try:
            cursor.execute(query)
            results = cursor.fetchall()

        except Exception as e:
            self.module.fail_json(msg="Cannot execute SQL '%s' : %s" % (query, to_native(e)))

        queries = []
        if results:
            q = "delete from mysql.user where user = '' and host = '{}'"
            for x in results:
                queries.append(q.format(x[0]))

        for q in queries:
            # self.module.log(msg="  query : {}".format(q))
            try:
                cursor.execute(q)

            except Exception as e:
                conn.rollback()
                self.module.fail_json(msg="Cannot execute SQL '%s' : %s" % (q, to_native(e)))

        conn.commit()
        conn.close()

        return (True, False, None)

    def _remove_test_database(self):
        """
        """
        cursor, conn, error, message = self._mysql_connect()

        if error:
            return (False, error, message)

        query = "drop database if exists test"

        # self.module.log(msg="  query : '{}'".format(query))

        try:
            cursor.execute(query)
            conn.commit()
            conn.close()

        except Exception as e:
            conn.rollback()
            self.module.fail_json(msg="Cannot execute SQL '%s' : %s" % (query, to_native(e)))

        return (True, False, None)

    def _exec(self, commands):
        """
          execute commands
        """
        self.module.log(msg="commands: {}".format(commands))

        rc, out, err = self.module.run_command(commands, check_rc=True)
        self.module.log(msg="  rc : '{}'".format(rc))
        self.module.log(msg="  out: '{}'".format(out))
        self.module.log(msg="  err: '{}'".format(err))
        return rc, out, err

    def _mysql_connect(self):
        """

        """
        config = {}

        config_file = self.mycnf_file

        if config_file and os.path.exists(config_file):
            config['read_default_file'] = config_file

        # If dba_user or dba_password are given, they should override the
        # config file
        if self.dba_root_username is not None:
            config['user'] = self.dba_root_username
        if self.dba_root_password is not None:
            config['passwd'] = self.dba_root_password

        # self.module.log(msg="config : {}".format(config))

        if mysql_driver is None:
            self.module.fail_json(msg=mysql_driver_fail_msg)

        try:
            db_connection = mysql_driver.connect(**config)

        except Exception as e:
            message = "unable to connect to database. "
            message += "check login_host, login_user and login_password are correct "
            message += "or {0} has the credentials. "
            message += "Exception message: {1}"
            message = message.format(config_file, to_native(e))

            self.module.log(msg=message)

            return (None, None, True, message)

        return (db_connection.cursor(), db_connection, False, "successful connected")

    def _parse_from_mysql_config_file(self, cnf):
        cp = configparser.ConfigParser()
        cp.read(cnf)
        return cp


# ---------------------------------------------------------------------------------------
# Module execution.
#

def main():
    ''' ... '''
    module = AnsibleModule(
        argument_spec=dict(
            disallow_anonymous_users=dict(required=False, type='bool'),
            disallow_test_database=dict(required=False, type='bool'),
            disallow_remote_root_login=dict(required=False, type='bool'),
            # dba_root_username=dict(required=False, type='str'),
            # dba_root_password=dict(required=False, type='str', no_log=True),
            mycnf_file=dict(required=False, type="str", default="/root/.my.cnf"),
        ),
        supports_check_mode=False,
    )

    module.log(msg="-------------------------------------------------------------")

    client = MariaDBSecure(module)
    result = client.run()

    module.log(msg="= result: {}".format(result))
    module.log(msg="-------------------------------------------------------------")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
