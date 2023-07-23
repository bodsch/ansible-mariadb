# python 3 headers, required if submitting to Ansible


from __future__ import (absolute_import, print_function)
__metaclass__ = type

import os
from ansible.utils.display import Display

# https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html
# https://blog.oddbit.com/post/2019-04-25-writing-ansible-filter-plugins/

display = Display()


class FilterModule(object):
    """
        Ansible file jinja2 tests
    """

    def filters(self):
        return {
            'support_tls': self.support_tls,
            'tls_directory': self.tls_directory,
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
