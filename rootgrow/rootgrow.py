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
import re
import syslog

split_dev = re.compile('([a-z/]*)(\d*)')
mounts = open('/proc/mounts', 'r').readlines()


def get_mount_point(device):
    for mount in mounts:
        if mount.startswith(device):
            return mount.split(' ')[1]


def is_mount_read_only(mountpoint):
    for mount in mounts:
        mount_values = mount.split(' ')
        if mount_values[1] == mountpoint:
            mount_opts = mount_values[3].split(',')
            return 'ro' in mount_opts


def resize_fs(fs_type, device):
    if fs_type.startswith('ext'):
        cmd = 'resize2fs {0}'.format(device)
        syslog.syslog(
            syslog.LOG_INFO, 'Resizing: "{0}"'.format(cmd)
        )
        os.system(cmd)
    elif fs_type == 'xfs':
        mnt_point = get_mount_point(device)
        cmd = 'xfs_growfs %s' % mnt_point
        syslog.syslog(
            syslog.LOG_INFO, 'Resizing: "{0}"'.format(cmd)
        )
        os.system(cmd)
    elif fs_type == 'btrfs':
        mnt_point = get_mount_point(device)
        # If the volume is read-only, the resize operation will fail even
        # though it's still probably wanted to do the resize. A feasible
        # work-around is to use snapper's .snapshots subdir (if exists)
        # instead of the volume path for the resize operation.
        if is_mount_read_only(mnt_point):
            if os.path.isdir('{}/.snapshots'.format(mnt_point)):
                cmd = 'btrfs filesystem resize max {}/.snapshots'.format(
                    mnt_point)
            else:
                syslog.syslog(
                    syslog.LOG_ERR,
                    "cannot resize read-only btrfs without snapshots"
                )
                return
        else:
            cmd = 'btrfs filesystem resize max {}'.format(mnt_point)
        syslog.syslog(
            syslog.LOG_INFO, 'Resizing: "{0}"'.format(cmd)
        )
        os.system(cmd)


def main():
    for mount in mounts:
        if ' / ' in mount:
            mount_dev = mount.split(' ')[0]
            fs = mount.split(' ')[2]
            try:
                dev, partition = split_dev.match(mount_dev).groups()
            except Exception:
                syslog.syslog(
                    syslog.LOG_ERR, 'match exception for "{0}"'.format(mount)
                )
                break
            if dev and partition:
                cmd = '/usr/sbin/growpart {0} {1}'.format(dev, partition)
                syslog.syslog(
                    syslog.LOG_INFO,
                    'Executing: "%s"' % cmd
                )
                os.system(cmd)
                resize_fs(fs, mount_dev)
            else:
                syslog.syslog(
                    syslog.LOG_ERR,
                    'could not match device and partition in "%s"' % mount
                )
