# python 3 headers, required if submitting to Ansible


from __future__ import (absolute_import, print_function)
__metaclass__ = type

import os
import re
# import json
from ansible.utils.display import Display
from ansible.module_utils.common._collections_compat import Mapping

# https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html
# https://blog.oddbit.com/post/2019-04-25-writing-ansible-filter-plugins/

display = Display()


class FilterModule(object):
    """
    """

    def filters(self):
        return {
            'support_tls': self.support_tls,
            'tls_directory': self.tls_directory,
            'detect_galera': self.detect_galera,
            'wsrep_cluster_address': self.wsrep_cluster_address,
            'system_user': self.system_user,
        }

    def support_tls(self, data):
        """
        """
        # display.vv(f"support_tls({data})")

        ssl_ca = data.get("ssl-ca", None)
        ssl_cert = data.get("ssl-cert", None)
        ssl_key = data.get("ssl-key", None)

        if ssl_ca and ssl_cert and ssl_key:
            return True
        else:
            return False

    def tls_directory(self, data):
        """
        """
        # display.vv(f"tls_directory({data})")

        directory = []

        ssl_ca = data.get("ssl-ca", None)
        ssl_cert = data.get("ssl-cert", None)
        ssl_key = data.get("ssl-key", None)

        if ssl_ca and ssl_cert and ssl_key:
            directory.append(os.path.dirname(ssl_ca))
            directory.append(os.path.dirname(ssl_cert))
            directory.append(os.path.dirname(ssl_key))

        directory = list(set(directory))

        if len(directory) == 1:
            return directory[0]

    def detect_galera(self, data, hostvars):
        """
        """
        display.vv(f"detect_galera({data}, hostvars)")
        result = dict(
            galera=False,
            cluster_members=[],
            cluster_primary_node="",
            cluster_replica_nodes=[],
            # primary = False
        )

        # cluster_names = []
        # cluster_primary_node = ""
        node_information = {}

        for x, v in hostvars.items():
            if isinstance(v, Mapping):
                v = dict(v)

            display.vv(f"  - {x}")
            _facts = v.get('ansible_facts')
            # display.vv(f"    ansible facts: {_facts}")
            display.vv(f"    facts default_ipv4  : {_facts.get('default_ipv4')}")
            display.vv(f"    facts default_ipv6  : {_facts.get('default_ipv6')}")
            display.vv(f"    ansible default_ipv4: {v.get('ansible_default_ipv4')}")
            display.vv(f"    ansible default_ipv6: {v.get('ansible_default_ipv6')}")

            # display.vv("------------------------------------------")
            # display.vv(f"    {json.dumps(v, indent=2, sort_keys=False)}")
            # display.vv("------------------------------------------")

        # self._galera_node_information(hostvars)

        if isinstance(data, dict):
            if data.get('wsrep_on', 'OFF') == 'ON':
                cluster_member = ""
                cluster_members = []
                # cluster_name = data.get("wsrep_node_name", "")
                cluster_adress = data.get("wsrep_cluster_address", "")
                bind_address = data.get("bind-address", "")

                # display.vv(f"- {cluster_adress}")

                pattern = re.compile(r"^gcomm://(?P<cluster_member>[0-9.,]+)$")
                result = re.search(pattern, cluster_adress)

                if result:
                    cluster_member = result.group('cluster_member')

                cluster_members = cluster_member.split(',')
                # remove empty elements
                cluster_members = list(filter(None, cluster_members))
                members_count = len(cluster_members)

                display.vv(f"- cluster_members: '{cluster_members}' : {members_count}")

                if members_count == 0:
                    # primary = True
                    primary_address = bind_address
                else:
                    primary_address = cluster_members[0]

                    # if primary_address == bind_address:
                    #     primary = True
                    # else:
                    #     primary = False

                if isinstance(hostvars, Mapping):
                    node_information = {x: v.get("ansible_default_ipv4", None).get("address", None) for x, v in hostvars.items() if v.get("ansible_default_ipv4", {}).get("address", None)}
                    display.vv(f"  node_information: '{node_information}'")

                primary_node = [x for x, v in node_information.items() if v == primary_address][0]
                replica_nodes = [x for x, v in node_information.items() if v != primary_address]

                result = dict(
                    galera=True,
                    cluster_members=cluster_members,
                    cluster_primary_node=primary_node,
                    cluster_replica_nodes=replica_nodes,
                    # primary = primary
                )

        # display.vv(f"= {result}")

        return result

    def wsrep_cluster_address(self, data):
        """
            input: [
                {'address': '10.29.0.10', 'port': '', 'name': 'primary'},
                {'address': '10.29.0.21', 'port': '', 'name': 'replica_1'},
                {'address': '10.29.0.22', 'port': '', 'name': 'replica_2'}
            ]

            output:
                '10.29.0.10:,10.29.0.21:,10.29.0.22:'
        """
        display.vv(f"wsrep_cluster_address({data})")
        result = None
        result = [f"{x.get('address')}" for x in data]

        result = ",".join(result)

        return result

    def _galera_node_information(self, data):
        """
        """
        display.vv("_galera_node_information(data)")
        result = dict()

        for hostname, values in data.items():
            display.vv(f"- {hostname}")
            display.vv(f"  {len(values)}")

            # host_data = data.get(hostname)
            #
            # display.vv(f"- {host_data}")
            #
            primary_address = values.get("ansible_default_ipv4", {}).get("address", None)
            host_name = values.get("hostname", None)

            if not host_name:
                host_name = hostname

            display.vv(f"- {primary_address} / {host_name}")

        display.vv(f"= {result}")
        return result

    def system_user(self, data, username):
        """ """
        display.vv(f"system_user({data}, {username})")

        result = [x for x in data if x.get('username') == username]
        if len(result) == 1:
            result = result[0]

        display.vv(f"= {result}")

        return result
