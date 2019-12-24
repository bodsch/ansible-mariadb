import pytest
import os
import testinfra.utils.ansible_runner

# import mysql.connector as mysql
# from mysql.connector import Error


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


@pytest.fixture()
def get_vars(host):
    defaults_files = "file=../../defaults/main.yml name=role_defaults"
    vars_files = "file=../../vars/main.yml name=role_vars"

    ansible_vars = host.ansible(
        "include_vars",
        defaults_files)["ansible_facts"]["role_defaults"]

    ansible_vars.update(host.ansible(
        "include_vars",
        vars_files)["ansible_facts"]["role_vars"])

    print(ansible_vars)

    return ansible_vars


def test_data_directory(host, get_vars):
    dir = host.file(get_vars['mariadb_datadir'])
    assert dir.exists
    assert dir.is_directory
    assert dir.user == get_vars['mariadb_log_file_group']
    assert dir.group == get_vars['mariadb_log_file_group']


def test_tmp_directory(host, get_vars):
    dir = host.file(get_vars['mariadb_tmpdir'])
    assert dir.exists
    assert dir.is_directory


def test_log_directory(host, get_vars):
    dir = host.file(get_vars['mariadb_log_directory'])
    assert dir.exists
    assert dir.is_directory
    assert dir.user == get_vars['mariadb_log_file_group']
    assert dir.group == get_vars['mariadb_log_file_group']


@pytest.mark.parametrize("dirs", [
    "/etc/mysql",
    "/etc/mysql/conf.d",
    "/etc/mysql/mariadb.conf.d"
])
def test_directories(host, dirs):
    d = host.file(dirs)
    assert d.is_directory
    assert d.exists


@pytest.mark.parametrize("files", [
    "/etc/mysql/my.cnf",
    "/etc/mysql/mariadb.cnf",
    "/etc/mysql/conf.d/mysql.cnf",
    "/etc/mysql/conf.d/mysqldump.cnf",
    "/etc/mysql/mariadb.conf.d/50-client.cnf",
    "/etc/mysql/mariadb.conf.d/50-mysql-clients.cnf",
    "/etc/mysql/mariadb.conf.d/50-mysqld_safe.cnf",
    "/etc/mysql/mariadb.conf.d/50-server.cnf",
    "/etc/mysql/mariadb.conf.d/59-client-security.cnf",
    "/etc/mysql/mariadb.conf.d/59-server-finetuning.cnf",
    "/etc/mysql/mariadb.conf.d/59-server-innodb.cnf",
    "/etc/mysql/mariadb.conf.d/59-server-logging.cnf",
    "/etc/mysql/mariadb.conf.d/59-server-replication.cnf",
    "/etc/mysql/mariadb.conf.d/59-server-security.cnf"
])
def test_files(host, files):
    f = host.file(files)
    assert f.exists
    assert f.is_file


def test_user(host):
    assert host.group("mysql").exists
    assert host.user("mysql").exists
    assert "mysql" in host.user("mysql").groups
    # assert host.user("mysql").shell == "/bin/false"
    # assert host.user("mysql").home == "/nonexistent"


# @pytest.mark.parametrize('protocol,port', [
#     ('unix', '/run/mysqld/mysqld.sock')
# ])
# def test_listening_socket(host, protocol, port):
#     socket = host.socket('%s://%s' % (protocol, port))
#     assert socket.is_listening
#
#
# def test_mariadb_running_and_enabled(host):
#     service = host.service("mariadb")
#     assert service.is_running
#     assert service.is_enabled
#
#
# def test_mysql_connetc(host):
#
#     conn = None
#     try:
#       conn = mysql.connect(
#         host = 'localhost',
#         user = 'monitoring',
#         password = 'monitoring',
#         database = 'monitoring')
#
#       assert conn.is_connected()
#
#       if conn.is_connected():
#         print('Connected to MySQL database')
#
#     except Error as e:
#       print(e)
#
#     finally:
#       if conn is not None and conn.is_connected():
#         conn.close()
