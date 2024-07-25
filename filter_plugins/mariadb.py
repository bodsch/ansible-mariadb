# python 3 headers, required if submitting to Ansible


from __future__ import (absolute_import, print_function)
__metaclass__ = type

import os
import re
from ansible.utils.display import Display

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
        }

    def support_tls(self, data):
        """
        """
        # display.v(f"support_tls({data})")

        ssl_ca   = data.get("ssl-ca", None)
        ssl_cert = data.get("ssl-cert", None)
        ssl_key  = data.get("ssl-key", None)

        if ssl_ca and ssl_cert and ssl_key:
            return True
        else:
            return False

    def tls_directory(self, data):
        """
        """
        # display.v(f"tls_directory({data})")

        directory = []

        ssl_ca   = data.get("ssl-ca", None)
        ssl_cert = data.get("ssl-cert", None)
        ssl_key  = data.get("ssl-key", None)

        if ssl_ca and ssl_cert and ssl_key:
            directory.append(os.path.dirname(ssl_ca))
            directory.append(os.path.dirname(ssl_cert))
            directory.append(os.path.dirname(ssl_key))

        directory = list(set(directory))

        if len(directory) == 1:
            return directory[0]

    def detect_galera(self, data):
        """
        """
        # display.v(f"detect_galera({data})")
        result = dict(
            galera = False,
            primary = False
        )

        if isinstance(data, dict):
            if data.get('wsrep_on', 'OFF') == 'ON':
                cluster_member = ""
                cluster_adress = data.get("wsrep_cluster_address", "")

                # display.v(f"- {cluster_adress}")

                pattern = re.compile(r"^gcomm://(?P<cluster_member>[0-9.,]+)$")
                result = re.search(pattern, cluster_adress)

                if result:
                    cluster_member = result.group('cluster_member')

                # display.v(f"- '{cluster_member}'")

                if len(cluster_member) == 0:
                    primary = True
                else:
                    primary = False

                result = dict(
                    galera = True,
                    primary = primary
                )

        # display.v(f"= {result}")

        return result
