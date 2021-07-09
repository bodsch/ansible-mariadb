
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

import json
import pytest
import os

import testinfra.utils.ansible_runner


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('replica_1')


def pp_json(json_thing, sort=True, indents=2):
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


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
    distribution = host.system_info.distribution
    release = host.system_info.release

    if distribution in ['debian', 'ubuntu']:
        os = "debian"
    elif distribution in ['centos', 'redhat', 'ol']:
        os = "redhat"
    elif distribution in ['arch']:
        os = "archlinux"

    print(" -> distibution {} / os {} / release {}".format(distribution, os, release))

    file_defaults = "file={}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)
    file_distibution = "file={}/vars/{}.yaml name=role_distibution".format(base_dir, os)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    distibution_vars = host.ansible("include_vars", file_distibution).get("ansible_facts").get("role_distibution")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(distibution_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def test_data_directory(host, get_vars):
    """
      configured datadir
    """
    directory = get_vars.get("mariadb_config_mysqld", {}).get("datadir", "/var/lib/mysql")
    user = "mysql"

    dir = host.file(directory)
    assert dir.is_directory
    assert dir.user == user
    assert dir.group == user


def test_tmp_directory(host, get_vars):
    """
      configured tmpdir
    """
    directory = get_vars.get("mariadb_config_mysqld", {}).get("tmpdir", "/tmp")

    dir = host.file(directory)
    assert dir.is_directory


def test_log_directory(host, get_vars):
    """
      configured logdir
    """
    error_log_file = get_vars.get("mariadb_config_mysqld", {}).get("log_error", "/var/log/mysql/error.log")
    user = "mysql"

    dir = host.file(os.path.dirname(error_log_file))
    assert dir.is_directory
    assert dir.user == user


def test_directories(host, get_vars):
    """
      used config directory

      debian based: /etc/mysql
      redhat based: /etc/my.cnf.d
      arch based  : /etc/my.cnf.d
    """
    pp_json(get_vars)

    directories = [
        get_vars.get("mariadb_config_dir"),
        get_vars.get("mariadb_config_include_dir")
    ]

    for dirs in directories:
        d = host.file(dirs)
        assert d.is_directory


def test_files(host, get_vars):
    """
      created config files
    """
    files = [
        get_vars.get("mariadb_config_file"),
        "{}/mysql.cnf".format(get_vars.get("mariadb_config_include_dir"))
    ]

    for _file in files:
        f = host.file(_file)
        assert f.is_file


def test_user(host, get_vars):
    """
      created user
    """
    shell = '/bin/false'

    distribution = host.system_info.distribution

    if distribution in ['centos', 'redhat', 'ol']:
        shell = "/sbin/nologin"
    elif distribution == "arch":
        shell = "/usr/bin/nologin"

    user_name = "mysql"
    u = host.user(user_name)
    g = host.group(user_name)

    assert g.exists
    assert u.exists
    assert user_name in u.groups
    assert u.shell == shell


def test_service_running_and_enabled(host, get_vars):
    """
      running service
    """
    service_name = get_vars.get("mariadb_service")

    service = host.service(service_name)
    assert service.is_running
    assert service.is_enabled
