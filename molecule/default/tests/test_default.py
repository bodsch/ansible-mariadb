import pytest
import os
import yaml
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


@pytest.fixture()
def AnsibleVars(host):
    all_vars = host.ansible.get_variables()
    return all_vars


@pytest.fixture()
def AnsibleDefaults():
    with open("../../defaults/main.yml", 'r') as stream:
        return yaml.load(stream)


def test_installation_directory(host, AnsibleVars):
    dir = host.file(AnsibleVars['mariadb_datadir'])
    # result = host.ansible('debug','var=kafka_final_path')
    # dir = host.file(result['kafka_final_path'])
    assert dir.exists
    assert dir.is_directory
    assert dir.user == AnsibleVars['mariadb_log_file_group']
    assert dir.group == AnsibleVars['mariadb_log_file_group']


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
    "/etc/mysql/conf.d/mariadb.cnf"
])
def test_files(host, files):
    f = host.file(files)
    assert f.exists
    assert f.is_file


def test_user(host):
    assert host.group("mysq").exists
    assert host.user("mysql").exists
    assert "mysql" in host.user("mysq").groups
    assert host.user("mysq").shell == "/bin/false"
    assert host.user("mysq").home == ""
