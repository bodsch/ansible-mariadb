#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2020-2024, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, print_function
import shutil
import os
import grp
import pwd

# from ansible.module_utils import distro
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}


class MariadbDataDirectories(object):
    """
        Main Class
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.source = module.params.get("source")
        self.destination = module.params.get("destination")

    def get_file_ownership(self, filename):
        return (
            pwd.getpwuid(os.stat(filename).st_uid).pw_name,
            grp.getgrgid(os.stat(filename).st_gid).gr_name
        )

    def run(self):
        if self.source == self.destination:
            return dict(
                changed=False,
                failed=False,
                msg="source '{}' and destination '{}' are the same".format(
                    self.source, self.destination)
            )

        if os.path.exists(self.destination):
            return dict(
                failed=False,
                changed=False,
                msg="directory {} already exists".format(self.destination)
            )

        # info = Path(self.source)
        # owner = info.owner()
        # group = info.group()

        owner, group = self.get_file_ownership(self.source)

        self.module.log(msg="  owner: {} | group: {}".format(owner, group))

        try:
            shutil.copytree(self.source, self.destination)

            for root, dirs, files in os.walk(self.destination):
                shutil.chown(root, owner, group)
                for item in dirs:
                    shutil.chown(os.path.join(root, item), owner, group)
                for item in files:
                    shutil.chown(os.path.join(root, item), owner, group)

            os.rename(self.source, "{}.dist".format(self.source))

        # Directories are the same
        except shutil.Error as e:
            self.module.log(msg="  Directory not copied. Error: {}".format(e))
        # Any error saying that the directory doesn't exist
        except OSError as e:
            self.module.log(msg="  Directory not copied. Error: {}".format(e))

        return dict(
            changed=True,
            failed=False,
            msg="directory {} synced to {}".format(self.source, self.destination)
        )


def main():
    """
    """
    specs = dict(
        source=dict(
            required=False,
            type='path',
            default='/var/lib/mysql'
        ),
        destination=dict(
            required=True,
            type='path'
        ),
    )

    module = AnsibleModule(
        argument_spec=specs,
        supports_check_mode=False,
    )

    helper = MariadbDataDirectories(module)
    result = helper.run()

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
