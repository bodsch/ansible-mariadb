
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
    password: secret
    encrypted: false
    host: 127.0.0.1
    priv: *.*:USAGE
```

### monitoring

```yaml
mariadb_monitoring:
  enabled: true
  system_user: "nobody"
  username: 'monitoring'
  password: '8WOMmRWWYHPR'
```

### replication

Enables and configures replication between 2 or more mariadb instances.

```yaml
mariadb_replication:
  # 'master' or 'replica'
  role: ''
  # hostname or IP for the master node
  master: ''
  # Same keys as `mariadb_users` above.
  user: {}
```

**ATTENTION: The password for replication must not be longer than 32 characters!**

[see](https://dev.mysql.com/doc/refman/5.6/en/change-master-to.html)

The following table shows the maximum permissible length for the string-valued options.
| Option          | Maximum Length |
| :----           | :----          |
| MASTER_PASSWORD | 32             |

For example:

```yaml
mariadb_replication:
  user:
    name: replication
    password: "vkxHlCVMHAEtEFkEB9pspPB3N"
    encrypted: false
```

### mysql tuner

```yaml
mariadb_mysqltuner: true
```



```yaml

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
