
# Ansible Role:  `mariadb`


Installs and configure a mariadb on varoius linux systems.

Implement also an monitoring user with own table.


[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bodsch/ansible-mariadb/CI)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-mariadb)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-mariadb)][releases]

[ci]: https://github.com/bodsch/ansible-mariadb/actions
[issues]: https://github.com/bodsch/ansible-mariadb/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-mariadb/releases


## tested operating systems

* Debian 9 / 10
* Ubuntu 18.04 / 20.04
* CentOS 8
* Oracle Linux 8
* Arch Linux


## usage

### use and create own data directory

```yaml
mariadb_datadir: /var/lib/mysql
```

### create databases

```yaml
mariadb_databases:
  - name: example
    collation: utf8_general_ci
    encoding: utf8
```

### create users

```yaml
mariadb_users:
  - name: example
    host: 127.0.0.1
    password: secret
    priv: *.*:USAGE
```

### monitoring

```yaml
mariadb_monitoring: true
mariadb_monitoring_user: 'nobody'
```

### mysql tuner

```yaml
mariadb_mysqltuner: true
```



```yaml
mariadb_use_external_repo: true
mariadb_version: 10.4

mariadb_debian_repo: "http://mirror.netcologne.de/mariadb/repo"

# Set this to the user ansible is logging in as - should have root
# or sudo access
mariadb_user_home: ''
mariadb_user_name: ''
mariadb_user_password: ''

# The default root user installed by mysql - almost always root
mariadb_root_home: /root
mariadb_root_username: root
mariadb_root_password: root

# Set this to `true` to forcibly update the root password.
mariadb_root_password_update: true
mariadb_user_password_update: false

mariadb_enabled_on_startup: true

# update my.cnf. each time role is run? true | false
overwrite_global_mycnf: true

# MySQL connection settings.
mariadb_port: 3306
mariadb_bind_address: '127.0.0.1'
mariadb_skip_name_resolve: true

mariadb_tmpdir: /tmp
mariadb_sql_mode: ''

mariadb_configure_swappiness: true
mariadb_swappiness: 0

# The following variables have a default value depending on operating system.
# mariadb_pid_file: /var/run/mysqld/mysqld.pid
# mariadb_socket: /var/lib/mysql/mysql.sock

# Log file settings.
mariadb_log_file_group: mysql

# Slow query log settings.
mariadb_slow_query_log_enabled: false
mariadb_slow_query_time: "2"
# The following variable has a default value depending on operating system.
# mariadb_slow_query_log_file: /var/log/mysql-slow.log

# Memory settings (default values optimized ~512MB RAM).
mariadb_key_buffer_size: "256M"
mariadb_max_allowed_packet: "64M"
mariadb_table_open_cache: "256"
mariadb_sort_buffer_size: "1M"
mariadb_read_buffer_size: "1M"
mariadb_read_rnd_buffer_size: "4M"
mariadb_myisam_sort_buffer_size: "64M"
mariadb_thread_cache_size: "8"
mariadb_query_cache_type: "0"
mariadb_query_cache_size: "16M"
mariadb_query_cache_limit: "3M"
mariadb_max_connections: "15"
# When making adjustments, make mariadb_tmp_table_size and mariadb_max_heap_table_size equal
mariadb_tmp_table_size: "64M"
mariadb_max_heap_table_size: "64M"
mariadb_group_concat_max_len: "1024"
mariadb_join_buffer_size: "262144"

# Other settings.
mariadb_lower_case_table_names: "0"
mariadb_wait_timeout: "28800"
mariadb_event_scheduler_state: "OFF"

# InnoDB settings.
mariadb_innodb_file_per_table: "1"
mariadb_supports_innodb_large_prefix: false
# Set .._buffer_pool_size up to 80% of RAM but beware of setting too high.
mariadb_innodb_buffer_pool_size: "256M"
# Set .._log_file_size to 25% of buffer pool size.
mariadb_innodb_log_file_size: "32M"
mariadb_innodb_log_buffer_size: "8M"
mariadb_innodb_flush_log_at_trx_commit: "1"
mariadb_innodb_lock_wait_timeout: "50"

# These settings require MySQL > 5.5.
mariadb_innodb_large_prefix: "1"

# The parameter innodb_file_format is deprecated and has no effect.
# It may be removed in future releases.
# See https://mariadb.com/kb/en/library/xtradbinnodb-file-format/
# default: barracuda
mariadb_innodb_file_format: ''

mariadb_innodb_data_file_path: ibdata1:10M:autoextend:max:128M

# mysqldump settings.
mariadb_mysqldump_max_allowed_packet: "64M"

# Logging settings.
# set an *FILE* for query logging
mariadb_log: ""

# The following variables have a default value depending on operating system.
# mariadb_log_error: /var/log/mysql/mysql.err
# mariadb_syslog_tag: mysql

# Replication settings (replication is only enabled if master/user have values).
mariadb_server_id: "1"
mariadb_max_binlog_size: "100M"
mariadb_binlog_format: "ROW"
mariadb_expire_logs_days: "10"
mariadb_replication_role: ''
mariadb_replication_master: ''
# Same keys as `mariadb_users` above.
mariadb_replication_user: []

mariadb_default_character_set: utf8mb4
mariadb_character_set_server: utf8mb4
mariadb_collation_server: utf8mb4_general_ci
```


## Tests

Tests can be performed with `molecule` and `tox`.
`tox` supports here with a test matrix, so that different Ansible versions can be used.

see also [Actions](https://github.com/bodsch/ansible-mariadb/actions)

```bash
tox -e py39-ansible210 -- molecule test
```

## License

[Apache](LICENSE)
