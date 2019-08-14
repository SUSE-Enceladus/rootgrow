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
import subprocess
import syslog

from rootgrow.resizefs import resize_fs


def get_root_device():
    result = subprocess.run(
        ['findmnt', '-n', '-f', '-o', 'SOURCE', '/'],
        stdout=subprocess.PIPE
    )
    return result.stdout.strip().decode()


def get_root_filesystem_type(root_device):
    result = subprocess.run(
        ['blkid', '-s', 'TYPE', '-o', 'value', root_device],
        stdout=subprocess.PIPE
    )
    return result.stdout.strip().decode()


def get_disk_device_from_root(root_device):
    result = subprocess.run(
        ['lsblk', '-p', '-n', '-r', '-s', '-o', 'NAME,TYPE', root_device],
        stdout=subprocess.PIPE
    )
    for device_info in result.stdout.decode().split(os.linesep):
        device_list = device_info.split()
        if device_list and device_list[1] == 'disk':
            return device_list[0]


def get_partition_id_from_root(disk_device, root_device):
    result = subprocess.run(
        ['lsblk', '-p', '-n', '-r', '-o', 'NAME', disk_device],
        stdout=subprocess.PIPE
    )
    partition_index = 0
    for device in result.stdout.decode().split(os.linesep):
        if device:
            if device == root_device:
                return partition_index
            partition_index = partition_index + 1


def main():
    try:
        root_device = get_root_device()
        if root_device:
            root_fs = get_root_filesystem_type(root_device)
            root_disk = get_disk_device_from_root(root_device)
            root_part = get_partition_id_from_root(root_disk, root_device)
            growpart = '/usr/sbin/growpart {0} {1}'.format(
                root_disk, root_part
            )
            syslog.syslog(
                syslog.LOG_INFO, 'Executing: "{0}"'.format(growpart)
            )
            os.system(growpart)
            resize_fs(root_fs, root_device)
    except Exception as issue:
        syslog.syslog(
            syslog.LOG_ERR, 'rootgrow failed with: {0}'.format(issue)
        )
