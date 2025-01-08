#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Balazs Pocze <banyek@gawker.com>
# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# Copyright: (c) 2023-2024, Bodo Schulz <bodo@boone-schulz.de>
# Certain parts are taken from Mark Theunissen's mysqldb module
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

import os
import warnings

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.mysql import (
    mysql_driver,
    mysql_driver_fail_msg,
    mysql_common_argument_spec
)
from ansible.module_utils._text import to_native
from distutils.version import LooseVersion

__metaclass__ = type


DOCUMENTATION = r'''
---
module: mysql_replication
short_description: Manage mariad replication
description:
- Manages mariadb server replication, replica, primary status, get and change primary host.
  Migrated from original ansible ansible_collections.community.mysql
author:
- Balazs Pocze (@banyek)
- Andrew Klychkov (@Andersson007)
- Bodo Schulz
options:
  mode:
    description:
    - Module operating mode. Could be
      C(change_primary) (CHANGE PRIMARY | MASTER TO),
      C(get_primary) (SHOW PRIMARY | MASTER STATUS),
      C(get_replica) (SHOW REPLICA | SLAVE STATUS),
      C(start_replica) (START REPLICA | SLAVE),
      C(stop_replica) (STOP REPLICA | SLAVE),
      C(reset_primary) (RESET PRIMARY | MASTER),
      C(reset_replica) (RESET REPLICA | SLAVE),
      C(reset_replica_all) (RESET REPLICA | SLAVE ALL).
    type: str
    choices:
    - change_primary
    - get_primary
    - get_replica
    - start_replica
    - stop_replica
    - reset_primary
    - reset_replica
    - reset_replica_all
    default: get_replica
  primary_host:
    description:
    - Same as the C(MASTER_HOST) mariadb variable.
    type: str
  primary_user:
    description:
    - Same as the C(MASTER_USER) mariadb variable.
    type: str
  primary_password:
    description:
    - Same as the C(MASTER_PASSWORD) mariadb variable.
    type: str
  primary_port:
    description:
    - Same as the C(MASTER_PORT) mariadb variable.
    type: int
  primary_connect_retry:
    description:
    - Same as the C(MASTER_CONNECT_RETRY) mariadb variable.
    type: int
  primary_log_file:
    description:
    - Same as the C(MASTER_LOG_FILE) mariadb variable.
    type: str
  primary_log_pos:
    description:
    - Same as the C(MASTER_LOG_POS) mariadb variable.
    type: int
  relay_log_file:
    description:
    - Same as mariadb variable.
    type: str
  relay_log_pos:
    description:
    - Same as mariadb variable.
    type: int
  primary_ssl:
    description:
    - Same as the C(MASTER_SSL) mariadb variable.
    - When setting it to C(yes), the connection attempt only succeeds
      if an encrypted connection can be established.
    - For details, refer to
      L(MySQL encrypted replication documentation,https://dev.mysql.com/doc/refman/8.0/en/replication-solutions-encrypted-connections.html).
    type: bool
    default: false
  primary_ssl_ca:
    description:
    - Same as the C(MASTER_SSL_CA) mysql variable.
    - For details, refer to
      L(MySQL encrypted replication documentation,https://dev.mysql.com/doc/refman/8.0/en/replication-solutions-encrypted-connections.html).
    type: str
  primary_ssl_capath:
    description:
    - Same as the C(MASTER_SSL_CAPATH) mysql variable.
    - For details, refer to
      L(MySQL encrypted replication documentation,https://dev.mysql.com/doc/refman/8.0/en/replication-solutions-encrypted-connections.html).
    type: str
  primary_ssl_cert:
    description:
    - Same as the C(MASTER_SSL_CERT) mysql variable.
    - For details, refer to
      L(MySQL encrypted replication documentation,https://dev.mysql.com/doc/refman/8.0/en/replication-solutions-encrypted-connections.html).
    type: str
  primary_ssl_key:
    description:
    - Same as the C(MASTER_SSL_KEY) mysql variable.
    - For details, refer to
      L(MySQL encrypted replication documentation,https://dev.mysql.com/doc/refman/8.0/en/replication-solutions-encrypted-connections.html).
    type: str
  primary_ssl_cipher:
    description:
    - Same as the C(MASTER_SSL_CIPHER) mysql variable.
    - Specifies a colon-separated list of one or more ciphers permitted by the replica for the replication connection.
    - For details, refer to
      L(MySQL encrypted replication documentation,https://dev.mysql.com/doc/refman/8.0/en/replication-solutions-encrypted-connections.html).
    type: str
  primary_auto_position:
    description:
    - Whether the host uses GTID based replication or not.
    - Same as the C(MASTER_AUTO_POSITION) mysql variable.
    type: bool
    default: false
  primary_use_gtid:
    description:
    - Configures the replica to use the MariaDB Global Transaction ID.
    - C(disabled) equals MASTER_USE_GTID=no command.
    - To find information about available values see
      U(https://mariadb.com/kb/en/library/change-master-to/#master_use_gtid).
    - Available since MariaDB 10.0.2.
    - C(replica_pos) has been introduced in MariaDB 10.5.1 and
      it is an alias for C(slave_pos).
    choices: [current_pos, replica_pos, disabled]
    type: str
    version_added: '0.1.0'
  primary_delay:
    description:
    - Time lag behind the primary's state (in seconds).
    - Same as the C(MASTER_DELAY) mysql variable.
    - Available from MySQL 5.6.
    - For more information see U(https://mariadb.com/kb/en/delayed-replication/).
    type: int
    version_added: '0.1.0'
  connection_name:
    description:
    - Name of the primary connection.
    - Supported from MariaDB 10.0.1.
    - Mutually exclusive with I(channel).
    - For more information see U(https://mariadb.com/kb/en/multi-source-replication/).
    type: str
    version_added: '0.1.0'
  channel:
    description:
    - Name of replication channel.
    - Multi-source replication is supported from MySQL 5.7.
    - Mutually exclusive with I(connection_name).
    - For more information see U(https://mariadb.com/kb/en/multi-source-replication/).
    type: str
    version_added: '0.1.0'
  fail_on_error:
    description:
    - Fails on error when calling mysql.
    type: bool
    default: False
    version_added: '0.1.0'

notes:
- If an empty value for the parameter of string type is needed, use an empty string.

extends_documentation_fragment:
- community.mysql.mysql


seealso:
- module: community.mysql.mysql_info
- name: MySQL replication reference
  description: Complete reference of the MySQL replication documentation.
  link: https://mariadb.com/kb/en/replication-cluster-multi-master/
- name: MySQL encrypted replication reference.
  description: Setting up MySQL replication to use encrypted connection.
  link: https://mariadb.com/kb/en/replication-with-secure-connections/
- name: MariaDB replication reference
  description: Complete reference of the MariaDB replication documentation.
  link: https://mariadb.com/kb/en/setting-up-replication/
'''

EXAMPLES = r'''
- name: Stop mysql replica thread
  mariadb_replication:
    mode: stop_replica

- name: Get primary binlog file name and binlog position
  mariadb_replication:
    mode: get_primary

- name: Change primary to primary server 192.0.2.1 and use binary log 'mysql-bin.000009' with position 4578
  mariadb_replication:
    mode: change_primary
    primary_host: 192.0.2.1
    primary_log_file: mysql-bin.000009
    primary_log_pos: 4578

- name: Check replica status using port 3308
  mariadb_replication:
    mode: get_replica
    login_host: ansible.example.com
    login_port: 3308

- name: On MariaDB change primary to use GTID current_pos
  mariadb_replication:
    mode: change_primary
    primary_use_gtid: current_pos

- name: Change primary to use replication delay 3600 seconds
  mariadb_replication:
    mode: change_primary
    primary_host: 192.0.2.1
    primary_delay: 3600

- name: Start MariaDB replica with connection name primary-1
  mariadb_replication:
    mode: startreplica
    connection_name: primary-1

- name: Stop replication in channel primary-1
  mariadb_replication:
    mode: stop_replica
    channel: primary-1

- name: >
    Run RESET MASTER command which will delete all existing binary log files
    and reset the binary log index file on the primary
  mariadb_replication:
    mode: reset_primary

- name: Run start replica and fail the task on errors
  mariadb_replication:
    mode: start_replica
    connection_name: primary-1
    fail_on_error: true

- name: Change primary and fail on error (like when replica thread is running)
  mariadb_replication:
    mode: change_primary
    fail_on_error: true

'''

RETURN = r'''
queries:
  description: List of executed queries which modified DB's state.
  returned: always
  type: list
  sample: ["CHANGE MASTER TO MASTER_HOST='primary2.example.com',MASTER_PORT=3306"]
  version_added: '0.1.0'
'''


class MariadbReplication():
    """

    """
    executed_queries = []
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module

        self.login_password = self.module.params.get("login_password")
        self.login_username = self.module.params.get("login_user")
        self.login_unix_socket = self.module.params.get("login_unix_socket")
        self.mode = module.params.get("mode")
        self.primary_host = module.params.get("primary_host")
        self.primary_user = module.params.get("primary_user")
        self.primary_password = module.params.get("primary_password")
        self.primary_port = module.params.get("primary_port")
        self.primary_connect_retry = module.params.get("primary_connect_retry")
        self.primary_log_file = module.params.get("primary_log_file")
        self.primary_log_pos = module.params.get("primary_log_pos")
        self.relay_log_file = module.params.get("relay_log_file")
        self.relay_log_pos = module.params.get("relay_log_pos")
        self.primary_ssl = module.params.get("primary_ssl")
        self.primary_ssl_ca = module.params.get("primary_ssl_ca")
        self.primary_ssl_capath = module.params.get("primary_ssl_capath")
        self.primary_ssl_cert = module.params.get("primary_ssl_cert")
        self.primary_ssl_key = module.params.get("primary_ssl_key")
        self.primary_ssl_cipher = module.params.get("primary_ssl_cipher")
        self.primary_auto_position = module.params.get("primary_auto_position")
        self.ssl_cert = module.params.get("client_cert")
        self.ssl_key = module.params.get("client_key")
        self.ssl_ca = module.params.get("ca_cert")
        # check_hostname = module.params.get("check_hostname")
        self.connect_timeout = module.params.get('connect_timeout')
        self.config_file = module.params.get('config_file')
        self.primary_delay = module.params.get('primary_delay')

        if module.params.get("primary_use_gtid") == 'disabled':
            self.primary_use_gtid = 'no'
        else:
            self.primary_use_gtid = module.params.get("primary_use_gtid")
        self.connection_name = module.params.get("connection_name")
        self.channel = module.params.get("channel")
        self.fail_on_error = module.params.get("fail_on_error")

        self.primary_term = 'MASTER'
        self.replica_term = 'SLAVE'

        if self.primary_use_gtid == 'replica_pos':
            self.primary_use_gtid = 'slave_pos'

        # module.log(msg="  mode: {}".format(self.mode))

    def run(self):
        """
        """
        result = dict(failed=True)

        if mysql_driver is None:
            self.module.fail_json(msg=mysql_driver_fail_msg)
        else:
            warnings.filterwarnings('error', category=mysql_driver.Warning)

        cursor, conn, error, message = self._mysql_connect()

        if error:
            return dict(
                failed=True,
                msg=message
            )

        self.prepare(cursor)

        if self.mode == 'get_primary':
            """
              get primary information
            """
            result = self.get_primary(cursor)

        elif self.mode == "get_replica":
            """
              get replica state
            """
            result = self.get_replica(cursor)

        elif self.mode == "change_primary":
            """
            """
            result = {}

            try:
                self.change_primary(cursor)
            except mysql_driver.Warning as e:
                result['warning'] = to_native(e)
            except Exception as e:
                self.module.fail_json(
                    msg=f"{to_native(e)}. Query == CHANGE MASTER TO ...")

            result['changed'] = True

            self.module.exit_json(queries=self.executed_queries, **result)

        elif self.mode in ("start_replica"):
            """
            """
            started = self.start_replica(cursor)
            if started is True:
                self.module.exit_json(
                    msg="Replica started ",
                    changed=True,
                    queries=self.executed_queries
                )
            else:
                self.module.exit_json(
                    msg="Replica already started (Or cannot be started)",
                    changed=False,
                    queries=self.executed_queries
                )

        elif self.mode in ("stop_replica"):
            """
            """
            stopped = self.stop_replica(cursor)

            if stopped is True:
                self.module.exit_json(
                    msg="Replica stopped",
                    changed=True,
                    queries=self.executed_queries
                )
            else:
                self.module.exit_json(
                    msg="Replica already stopped",
                    changed=False,
                    queries=self.executed_queries
                )

        elif self.mode in ("reset_primary"):
            """
            """
            reset = self.reset_primary(cursor)

            if reset is True:
                self.module.exit_json(
                    msg="Primary reset",
                    changed=True,
                    queries=self.executed_queries
                )
            else:
                self.module.exit_json(
                    msg="Primary already reset",
                    changed=False,
                    queries=self.executed_queries
                )

        elif self.mode in ("reset_replica"):
            """
            """
            reset = self.reset_replica(cursor)

            if reset is True:
                self.module.exit_json(
                    msg="Replica reset",
                    changed=True,
                    queries=self.executed_queries
                )
            else:
                self.module.exit_json(
                    msg="Replica already reset",
                    changed=False,
                    queries=self.executed_queries
                )

        elif self.mode in ("reset_replica_all"):
            """
            """
            reset = self.reset_replica_all(cursor)

            if reset is True:
                self.module.exit_json(
                    msg="Replica reset",
                    changed=True,
                    queries=self.executed_queries
                )
            else:
                self.module.exit_json(
                    msg="Replica already reset",
                    changed=False,
                    queries=self.executed_queries
                )

        warnings.simplefilter("ignore")

        return result

    def prepare(self, cursor):
        """
        """
        cursor.execute("SELECT VERSION() as version")

        curser_fetched = cursor.fetchone()

        if curser_fetched is not None:
            # self.module.log(f"- cursor: {curser_fetched} ({type(curser_fetched)})")

            if isinstance(curser_fetched, dict):
                version = curser_fetched["version"].lower()
            else:
                version = curser_fetched[0].lower()

            # self.module.log(f"- version: {LooseVersion(version)}")

            if LooseVersion(version) >= LooseVersion('10.5.1'):  # or LooseVersion(result) >= LooseVersion('8.0.22'):
                # self.primary_term = 'PRIMARY'
                self.replica_term = 'REPLICA'
                if self.primary_use_gtid == 'slave_pos':
                    self.primary_use_gtid = 'replica_pos'

    def get_primary(self, cursor):
        """
        """
        # self.module.log("get_primary()")

        result = dict()

        # if self.mode == 'getmaster':
        #     self.module.deprecate(
        #         '"getmaster" option is deprecated, use "getprimary" instead.',
        #          version='3.0.0', collection_name='community.mysql')

        # TODO: when it's available to change on MySQL's side,
        # change MASTER to PRIMARY using the approach from
        # get_replica_status() function. Same for other functions.
        query = f"SHOW {self.primary_term} STATUS"

        # self.module.log(msg=f"- query: {query}")

        cursor.execute(query)
        primary_status = cursor.fetchone()

        # self.module.log(msg="  status: {}".format(primary_status))

        if not isinstance(primary_status, dict):
            primary_status = dict(
                Is_Primary=False,
                msg="Server is not configured as mysql master"
            )
        else:
            primary_status['Is_Primary'] = True

        result = dict(
            queries=self.executed_queries,
            **primary_status
        )

        # self.module.log(msg="  result: {}".format(result))

        return result

    def get_replica(self, cursor):
        """
        """
        # self.module.log("get_replica()")

        result = dict()

        query = f"SHOW {self.replica_term} STATUS"

        if self.connection_name:
            query = f"SHOW {self.replica_term} '{self.connection_name}' STATUS"

        if self.channel:
            query += f" FOR CHANNEL '{self.channel}'"

        # self.module.log(msg=f"- query: {query}")

        cursor.execute(query)
        replica_status = cursor.fetchone()

        # self.module.log(msg="  status: {}".format(replica_status))

        if not isinstance(replica_status, dict):
            replica_status = dict(
                Is_Replica=False,
                msg="Server is not configured as mysql replica"
            )
        else:
            replica_status['Is_Replica'] = True

        result = dict(
            queries=self.executed_queries,
            **replica_status
        )

        # self.module.log(msg="  result: {}".format(result))

        return result

        # self.module.exit_json(queries=self.executed_queries, **status)

    def stop_replica(self, cursor):
        """
        """
        query = f'STOP {self.replica_term}'

        if self.connection_name:
            query = f"STOP {self.replica_term} '{self.connection_name}'"

        if self.channel:
            query += f" FOR CHANNEL '{self.channel}'"

        # self.module.log(msg="- query: {}".format(query))

        try:
            self.executed_queries.append(query)
            cursor.execute(query)
            stopped = True
        except mysql_driver.Warning as e:
            self.module.log(msg=f"WARNING: {to_native(e)}")
            stopped = False
        except Exception as e:
            if self.fail_on_error:
                self.module.fail_json(
                    msg=f"STOP REPLICA failed: {to_native(e)}"
                )
            stopped = False

        return stopped

    def reset_replica(self, cursor):
        """
        """
        query = f'RESET {self.replica_term}'

        if self.connection_name:
            query = f"RESET {self.replica_term} '{self.connection_name}'"

        if self.channel:
            query += f" FOR CHANNEL '{self.channel}'"

        # self.module.log(msg="- query: {}".format(query))

        try:
            self.executed_queries.append(query)
            cursor.execute(query)
            reset = True
        except mysql_driver.Warning as e:
            self.module.log(msg=f"WARNING: {to_native(e)}")
            reset = False
        except Exception as e:
            if self.fail_on_error:
                self.module.fail_json(
                    msg=f"RESET REPLICA failed: {to_native(e)}"
                )
            reset = False

        return reset

    def reset_replica_all(self, cursor):
        """
        """
        query = f'RESET {self.replica_term} ALL'

        if self.connection_name:
            query = f"RESET {self.replica_term} '{self.connection_name}' ALL"

        if self.channel:
            query += f" FOR CHANNEL '{self.channel}'"

        # self.module.log(msg="- query: {}".format(query))

        try:
            self.executed_queries.append(query)
            cursor.execute(query)
            reset = True
        except mysql_driver.Warning as e:
            self.module.log(msg=f"WARNING: {to_native(e)}")
            reset = False
        except Exception as e:
            if self.fail_on_error:
                self.module.fail_json(
                    msg=f"RESET REPLICA ALL failed: {to_native(e)}"
                )
            reset = False

        return reset

    def reset_primary(self, cursor):
        """
        """
        query = 'RESET MASTER'

        # self.module.log(msg="- query: {}".format(query))

        try:
            self.executed_queries.append(query)
            cursor.execute(query)
            reset = True
        except mysql_driver.Warning as e:
            self.module.log(msg=f"WARNING: {to_native(e)}")
            reset = False
        except Exception as e:
            if self.fail_on_error:
                self.module.fail_json(
                    msg=f"RESET MASTER failed: {to_native(e)}"
                )
            reset = False
        return reset

    def start_replica(self, cursor):
        """
        """
        query = f'START {self.replica_term}'

        if self.connection_name:
            query = f"START {self.replica_term} '{self.connection_name}'"

        if self.channel:
            query += f" FOR CHANNEL '{self.channel}'"

        # self.module.log(msg="- query: {}".format(query))

        try:
            self.executed_queries.append(query)
            cursor.execute(query)
            started = True
        except mysql_driver.Warning as e:
            self.module.log(msg=f"WARNING: {to_native(e)}")
            started = False
        except Exception as e:
            if self.fail_on_error:
                self.module.fail_json(
                    msg=f"START REPLICA failed: {to_native(e)}"
                )
            started = False

        return started

    def change_primary(self, cursor):
        """
        """
        chm = []
        if self.primary_host is not None:
            chm.append(f"MASTER_HOST='{self.primary_host}'")
        if self.primary_user is not None:
            chm.append(f"MASTER_USER='{self.primary_user}'")
        if self.primary_password is not None:
            chm.append(f"MASTER_PASSWORD='{self.primary_password}'")
        if self.primary_port is not None:
            chm.append(f"MASTER_PORT={self.primary_port}")
        if self.primary_connect_retry is not None:
            chm.append(f"MASTER_CONNECT_RETRY={self.primary_connect_retry}")
        if self.primary_log_file is not None:
            chm.append(f"MASTER_LOG_FILE='{self.primary_log_file}'")
        if self.primary_log_pos is not None:
            chm.append(f"MASTER_LOG_POS={self.primary_log_pos}")
        if self.primary_delay is not None:
            chm.append(f"MASTER_DELAY={self.primary_delay}")
        if self.relay_log_file is not None:
            chm.append(f"RELAY_LOG_FILE='{self.relay_log_file}'")
        if self.relay_log_pos is not None:
            chm.append(f"RELAY_LOG_POS={self.relay_log_pos}")
        if self.primary_ssl:
            chm.append("MASTER_SSL=1")
        if self.primary_ssl_ca is not None:
            chm.append(f"MASTER_SSL_CA='{self.primary_ssl_ca}'")
        if self.primary_ssl_capath is not None:
            chm.append(f"MASTER_SSL_CAPATH='{self.primary_ssl_capath}'")
        if self.primary_ssl_cert is not None:
            chm.append(f"MASTER_SSL_CERT='{self.primary_ssl_cert}'")
        if self.primary_ssl_key is not None:
            chm.append(f"MASTER_SSL_KEY='{self.primary_ssl_key}'")
        if self.primary_ssl_cipher is not None:
            chm.append(f"MASTER_SSL_CIPHER='{self.primary_ssl_cipher}'")
        if self.primary_auto_position:
            chm.append("MASTER_AUTO_POSITION=1")
        if self.primary_use_gtid is not None:
            chm.append(f"MASTER_USE_GTID={self.primary_use_gtid}")

        self.module.log(msg=f"  chm: {chm}")

        comma_chm = ','.join(chm)

        query = f"CHANGE MASTER TO {comma_chm}"

        if self.connection_name:
            query = f"CHANGE MASTER '{self.connection_name}' TO {comma_chm}"

        if self.channel:
            query += f" FOR CHANNEL '{self.channel}'"

        self.module.log(msg=f"- query: {query}")

        self.executed_queries.append(query)
        cursor.execute(query)

    def _mysql_connect(self):
        """
        """
        _mysql_cursor_param = 'cursor'

        config = {}

        config_file = self.config_file

        if config_file and os.path.exists(config_file):
            config['read_default_file'] = config_file

        # If dba_user or dba_password are given, they should override the
        # config file
        if self.login_username is not None:
            config['user'] = self.login_username
        if self.login_password is not None:
            config['passwd'] = self.login_password

        if self.login_unix_socket is not None and os.path.exists(self.login_unix_socket):
            config['unix_socket'] = self.login_unix_socket

        # self.module.log(msg=f"config : {config}")

        if mysql_driver is None:
            self.module.fail_json(msg=mysql_driver_fail_msg)

        try:
            db_connection = mysql_driver.connect(**config)

        except Exception as e:
            message = "unable to connect to database. "
            message += "check login_host, login_user and login_password are correct "
            message += f"or {config_file} has the credentials. "
            message += f"Exception message: {to_native(e)}"

            self.module.log(msg=message)

            return (None, None, True, message)

        return (
            db_connection.cursor(
                **{_mysql_cursor_param: mysql_driver.cursors.DictCursor}
            ),
            db_connection,
            False,
            "successful connected"
        )

    def _parse_from_mysql_config_file(self, cnf):
        cp = configparser.ConfigParser()
        cp.read(cnf)
        return cp


def main():
    """
    """
    specs = mysql_common_argument_spec()
    specs.update(
        mode=dict(
            type='str',
            default='get_replica', choices=[
                'get_primary',
                'get_replica',
                'change_primary',
                'stop_replica',
                'start_replica',
                'reset_primary',
                'reset_replica',
                'reset_replica_all',
            ]),
        primary_auto_position=dict(type='bool', default=False),
        primary_host=dict(type='str'),
        primary_user=dict(type='str'),
        primary_password=dict(type='str', no_log=True),
        primary_port=dict(type='int'),
        primary_connect_retry=dict(type='int'),
        primary_log_file=dict(type='str'),
        primary_log_pos=dict(type='int'),
        relay_log_file=dict(type='str'),
        relay_log_pos=dict(type='int'),
        primary_ssl=dict(type='bool', default=False),
        primary_ssl_ca=dict(type='str'),
        primary_ssl_capath=dict(type='str'),
        primary_ssl_cert=dict(type='str'),
        primary_ssl_key=dict(type='str', no_log=False),
        primary_ssl_cipher=dict(type='str'),
        primary_use_gtid=dict(type='str', choices=[
            'current_pos',
            'replica_pos',
            'slave_pos',
            'disabled']),
        primary_delay=dict(type='int'),
        connection_name=dict(type='str'),
        channel=dict(type='str'),
        fail_on_error=dict(type='bool', default=False),
    )

    module = AnsibleModule(
        argument_spec=specs,
        mutually_exclusive=[
            ['connection_name', 'channel']
        ],
    )

    # module.log(msg="-------------------------------------------------------------")

    client = MariadbReplication(module)
    result = client.run()

    # module.log(msg="= result: {}".format(result))
    # module.log(msg="-------------------------------------------------------------")

    module.exit_json(**result)


if __name__ == '__main__':
    main()
