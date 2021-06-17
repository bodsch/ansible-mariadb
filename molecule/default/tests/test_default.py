
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
import pytest
import os

import testinfra.utils.ansible_runner

import pprint
pp = pprint.PrettyPrinter()

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def base_directory():
    cwd = os.getcwd()

    if('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


@pytest.fixture()
def get_vars(host):
    """

    """
    base_dir, molecule_dir = base_directory()

    file_defaults = "file={}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def test_data_directory(host, get_vars):
    """
    """
    directory = get_vars.get('mariadb_datadir')
    user = get_vars.get('mariadb_log_file_group')
    pp.pprint(directory)
    pp.pprint(user)

    dir = host.file(directory)
    assert dir.exists
    assert dir.is_directory
    assert dir.user == user
    assert dir.group == user


def test_tmp_directory(host, get_vars):
    """
    """
    directory = get_vars.get('mariadb_tmpdir')

    dir = host.file(directory)
    assert dir.exists
    assert dir.is_directory


def test_log_directory(host, get_vars):
    """
    """
    directory = get_vars.get('mariadb_log_directory')
    user = get_vars.get('mariadb_log_file_group')

    pp.pprint(directory)
    pp.pprint(user)

    dir = host.file(directory)
    assert dir.exists
    assert dir.is_directory
    assert dir.user == user
    assert dir.group == user


@pytest.mark.parametrize("dirs", [
    "/etc/mysql",
    "/etc/mysql/conf.d",
    "/etc/mysql/mariadb.conf.d"
])
def test_directories(host, dirs):
    d = host.file(dirs)
    assert d.is_directory


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
    assert f.is_file


def test_user(host, get_vars):

    distribution = host.system_info.distribution

    if distribution in ['debian', 'ubuntu']:
        shell = '/bin/false'
    elif distribution in ['centos', 'redhat', 'ol']:
        shell = '/sbin/nologin'

    user_name = "mysql"
    u = host.user(user_name)
    g = host.group(user_name)

    assert g.exists
    assert u.exists
    assert user_name in u.groups
    assert u.shell == shell


def test_mariadb_running_and_enabled(host, get_vars):
    """
    """
    distribution = host.system_info.distribution

    if distribution == 'ubuntu':
        distribution = 'debian'
    elif distribution in ['centos', 'ol']:
        distribution = 'redhat'

    service_name = get_vars.get('_mariadb_service').get(distribution)

    service = host.service(service_name)
    assert service.is_running
    assert service.is_enabled


def test_listening_socket(host, get_vars):
    """
    """
    listening = host.socket.get_listening_sockets()

    for i in listening:
        pp.pprint(i)

    distribution = host.system_info.distribution
    release = host.system_info.release

    if distribution == 'ubuntu':
        distribution = 'debian'
    elif distribution in ['centos', 'ol']:
        distribution = 'redhat'

    socket_name = get_vars.get('_mariadb_socket').get(distribution)

    f = host.file(socket_name)
    assert f.exists

    for spec in (
        "tcp://127.0.0.1:3306",
        "unix://{}".format(socket_name)):

        socket = host.socket(spec)
        assert socket.is_listening

    # if not (distribution == 'debian' and release == '18.04'):
    #     socket_name = 'unix://{}'.format(socket_name)
    #     pp.pprint("  '{}'".format(socket_name))
    #
    #     socket = host.socket(socket_name)
    #     assert socket.is_listening
