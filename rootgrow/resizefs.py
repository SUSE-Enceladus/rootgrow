# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of rootgrow
#
# rootgrow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rootgrow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rootgrow.  If not, see <http://www.gnu.org/licenses/>
#
import os
import syslog
import subprocess


def get_mount_point(device):
    result = subprocess.run(
        ['findmnt', '-n', '-f', '-o', 'TARGET', device],
        stdout=subprocess.PIPE
    )
    return result.stdout.strip().decode()


def get_mount_options(device):
    result = subprocess.run(
        ['findmnt', '-n', '-f', '-o', 'OPTIONS', device],
        stdout=subprocess.PIPE
    )
    return result.stdout.decode().strip().split(',')


def resize_fs(fs_type, device):
    if fs_type.startswith('ext'):
        cmd = 'resize2fs {0}'.format(device)
        syslog.syslog(
            syslog.LOG_INFO, 'Resizing: "{0}"'.format(cmd)
        )
        os.system(cmd)
    elif fs_type == 'xfs':
        mnt_point = get_mount_point(device)
        cmd = 'xfs_growfs {0}'.format(mnt_point)
        syslog.syslog(
            syslog.LOG_INFO, 'Resizing: "{0}"'.format(cmd)
        )
        os.system(cmd)
    elif fs_type == 'btrfs':
        mnt_point = get_mount_point(device)
        mnt_options = get_mount_options(device)
        # If the volume is read-only, the resize operation will fail even
        # though it's still probably wanted to do the resize. A feasible
        # work-around is to use snapper's .snapshots subdir (if exists)
        # instead of the volume path for the resize operation.
        if 'ro' in mnt_options:
            if os.path.isdir('{0}/.snapshots'.format(mnt_point)):
                cmd = 'btrfs filesystem resize max {0}/.snapshots'.format(
                    mnt_point
                )
            else:
                syslog.syslog(
                    syslog.LOG_ERR,
                    'cannot resize read-only btrfs without snapshots'
                )
                return
        else:
            cmd = 'btrfs filesystem resize max {0}'.format(mnt_point)
        syslog.syslog(
            syslog.LOG_INFO, 'Resizing: "{0}"'.format(cmd)
        )
        os.system(cmd)
