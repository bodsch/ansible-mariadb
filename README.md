
# Ansible Role:  `mariadb`


Installs and configure a mariadb on varoius linux systems.

Implement also an monitoring user with own table.


[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-mariadb/main.yml?branch=main)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-mariadb)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-mariadb)][releases]
[![Ansible Downloads](https://img.shields.io/ansible/role/d/bodsch/mariadb?logo=ansible)][galaxy]

[ci]: https://github.com/bodsch/ansible-mariadb/actions
[issues]: https://github.com/bodsch/ansible-mariadb/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-mariadb/releases
[galaxy]: https://galaxy.ansible.com/ui/standalone/roles/bodsch/mariadb/

## Requirements & Dependencies

Ansible Collections

- [bodsch.core](https://github.com/bodsch/ansible-collection-core)

```bash
ansible-galaxy collection install bodsch.core
```
or
```bash
ansible-galaxy collection install --requirements-file collections.yml
```

## tested operating systems

* ArchLinux
* Debian based
    - Debian 11 / 12
    - Ubuntu 22.04

> **RedHat-based systems are no longer officially supported! May work, but does not have to.**

## usage

### use and create own data directory

```yaml
mariadb_datadir: /var/lib/mysql
```

### create system users

To create a `.my.cnf` on an instance, `mariadb_system_users` can be used.

If no password is set, the associated task is skipped.


| variable   | description |
| :---       | :-----      |
| `username` | The user name for administrative access. |
| `password` | If no password is set, the associated task is skipped. |
| `home`     | The home directory under which a `.my.cnf` is created. |
| `update`   | Should the password be updated. |
| `ignore`   | If the entire process is to be ignored, `ignore` must be set to `true`. |

```yaml
mariadb_system_users:
  - username: root
    password: ""
    home: /root
    update: true
    ignore: true
```

### create databases

```yaml
mariadb_databases:
  - name: example
    collation: utf8_general_ci
    encoding: utf8
```

### create database users

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
  enabled: false
  role: '' # primary or replica
  primary: ''
  # Same keys as `mariadb_users` above.
  user:
    name: replication
    # The password must not be longer than 32 characters!
    # password: ""
    encrypted: false
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
  enabled: true
  role: 'primary'
  primary: 'primary.mariadb.internal'
  user:
    name: replication
    password: "vkxHlCVMHAEtEFkEB9pspPB3N"
    encrypted: false
```

**EVERY replica** should have a `mariadb_server_id` greater then `1`.

```yaml
mariadb_server_id: 2
```

### galera cluster

With a gallery cluster, starting the individual instances correctly is extremely important!  
One of the instances must be started first as the primary node. All subsequent nodes then replicate the information.  
A restart of the mariadb service must not destroy the cluster status, so they must be restarted **serially** and **not in parallel**!

Example configuration:

```yaml
mariadb_galera:
  node_addresses:
    - address: "10.29.0.10"
    - address: "10.29.0.21"
    - address: "10.29.0.22"
  sst:
    method: rsync
    auth:
      username: "sstuser"
      password: ""
  node:
    name: "{{ ansible_hostname }}"
    id: "{{ mariadb_server_id | default('1') }}"
    address: "{{ ansible_default_ipv4.address | default('127.0.0.1') }}"
  gtid_domain_id: "{{ mariadb_server_id | default('1') }}"

  provider_options:
    - debug=yes
    - gcache.size=512M
    - gcache.page_size=128M
    - gcache.recover=yes
    - gmcast.peer_timeout=PT10S
    - pc.announce_timeout=PT10S

```

(A fully functional configuration can be found under [molecule/galera-cluster](molecule/galera-cluster).)


### mysql tuner

```yaml
mariadb_mysqltuner: true
```


### default variables

see [default/main.yml](default/main.yml):

```yaml
mariadb_use_external_repo: false
mariadb_version: 10.4

mariadb_debian_repo: "http://mirror.netcologne.de/mariadb/repo"

mariadb_monitoring:
  enabled: false
  system_user: "nobody"
  username: 'monitoring'
  password: '8WOMmRWWYHPR'

mariadb_mysqltuner: false

mariadb_system_users:
  - username: root
    password: ""
    home: /root
    update: true
    ignore: true

mariadb_enabled_on_startup: true

# config settings
# every ini part like [mysqld, galera, embedded, ...] becomes an own segment
# for default configuration settings, see: vars/main.yml

# this is read by the standalone daemon and embedded servers
mariadb_config_server: {}

# This group is read by the client library
mariadb_config_client: {}

# These groups are read by MariaDB command-line tools
mariadb_config_mysql: {}

# this is only for the mysqld standalone daemon
mariadb_config_mysqld:
  socket: "{{ mariadb_socket }}"
  skip-external-locking:
  # Skip reverse DNS lookup of clients
  skip-name-resolve: 1
  # enable performance schema
  performance_schema: 1

# NOTE: This file is read only by the traditional SysV init script, not systemd.
mariadb_config_mysqld_safe: {}

mariadb_config_mysqldump: {}

mariadb_config_galera: {}

# this is only for embedded server
mariadb_config_embedded: {}

mariadb_config_custom:
  # This group is only read by MariaDB servers, not by MySQL.
  mariadb: {}
  # This group is only read by MariaDB-$VERSION servers.
  #mariadb-10.1: {}
  #mariadb-10.5: {}
  # This group is *never* read by mysql client library
  client-mariadb: {}
  mysql_upgrade: {}
  mysqladmin: {}
  mysqlbinlog: {}
  mysqlcheck: {}
  mysqlimport: {}
  mysqlshow: {}
  mysqlslap: {}

mariadb_configure_swappiness: true
mariadb_swappiness: 0

# Databases.
mariadb_databases: []

# Users.
mariadb_users: []

# Replication settings (replication is only enabled if master/user have values).
mariadb_server_id: "1"

mariadb_replication:
  # enable / disable replication
  enabled: false
  # 'master' or 'replica'
  role: ''
  # hostname or IP for the master node
  primary: ''
  # Same keys as `mariadb_users` above.
  user: []
  
mariadb_galera:
  node_addresses: []
  sst:
    method: rsync
    auth:
      username: "sstuser"
      password: ""
  node:
    name: "{{ ansible_hostname }}"
    id: "{{ mariadb_server_id | default('1') }}"
    address: "{{ ansible_default_ipv4.address | default('127.0.0.1') }}"
  gtid_domain_id: "{{ mariadb_server_id | default('1') }}"
  provider_options: []
```

## Tests

Tests can be performed with `molecule` and `tox`.
`tox` supports here with a test matrix, so that different Ansible versions can be used.

see also [Actions](https://github.com/bodsch/ansible-mariadb/actions)

```bash
tox -e py39-ansible210 -- molecule test
```

## Contribution

Please read [Contribution](CONTRIBUTING.md)

## Development,  Branches (Git Tags)

The `master` Branch is my *Working Horse* includes the "latest, hot shit" and can be complete broken!

If you want to use something stable, please use a [Tagged Version](https://github.com/bodsch/ansible-mariadb/tags)!

## Author

- Bodo Schulz

## License

[Apache](LICENSE)

**FREE SOFTWARE, HELL YEAH!**
