import unittest
import syslog
from pytest import raises
from mock import (
    patch, Mock, call
)

from rootgrow.rootgrow import (
    get_disk_device_from_root, get_partition_id_from_root, get_root_device,
    get_root_filesystem_type, main
)


class TestRootGrow(unittest.TestCase):
    @patch('os.system')
    @patch('subprocess.Popen')
    def test_rootgrow_main(self, mock_subprocess_popen, mock_os_system):
        root_device = Mock()
        attrs = {'communicate.return_value': (b'/dev/sda3', b'')}
        root_device.configure_mock(**attrs)
        root_fs = Mock()
        attrs = {'communicate.return_value': (b'ext3', b'')}
        root_fs.configure_mock(**attrs)
        root_disk = Mock()
        attrs = {'communicate.return_value': (
            b'/dev/sda', b'')}
        root_disk.configure_mock(**attrs)
        mock_subprocess_popen.side_effect = [
            root_device, root_fs, root_disk
        ]
        main()
        assert mock_subprocess_popen.call_args_list == [
            call(
                ['findmnt', '-n', '-f', '-o', 'SOURCE', '/'],
                stdout=-1, stderr=-1
            ),
            call(
                ['blkid', '-s', 'TYPE', '-o', 'value', '/dev/sda3'],
                stdout=-1, stderr=-1
            ),
            call(
                [
                    'lsblk', '-n', '-p', '-o',
                    'PKNAME', '/dev/sda3'
                ],
                stdout=-1, stderr=-1
            )
        ]
        assert mock_os_system.call_args_list == [
            call('/usr/sbin/growpart /dev/sda 3'),
            call('resize2fs /dev/sda3')
        ]

    @patch('os.system')
    @patch('subprocess.Popen')
    def test_rootgrow_main_nvme(self, mock_subprocess_popen, mock_os_system):
        root_device = Mock()
        attrs = {'communicate.return_value': (b'/dev/nvme0n1p3', b'')}
        root_device.configure_mock(**attrs)
        root_fs = Mock()
        attrs = {'communicate.return_value': (b'xfs', b'')}
        root_fs.configure_mock(**attrs)
        root_disk = Mock()
        attrs = {'communicate.return_value': (
            b'/dev/nvme0n1', b'')}
        root_disk.configure_mock(**attrs)
        root_fs_mnt = Mock()
        attrs = {'communicate.return_value': (b'/', b'')}
        root_fs_mnt.configure_mock(**attrs)
        mock_subprocess_popen.side_effect = [
            root_device, root_fs, root_disk, root_fs_mnt
        ]
        main()
        assert mock_subprocess_popen.call_args_list == [
            call(
                ['findmnt', '-n', '-f', '-o', 'SOURCE', '/'],
                stdout=-1, stderr=-1
            ),
            call(
                ['blkid', '-s', 'TYPE', '-o', 'value', '/dev/nvme0n1p3'],
                stdout=-1, stderr=-1
            ),
            call(
                [
                    'lsblk', '-n', '-p', '-o',
                    'PKNAME', '/dev/nvme0n1p3'
                ],
                stdout=-1, stderr=-1
            ),
            call(
                ['findmnt', '-n', '-f', '-o', 'TARGET', '/dev/nvme0n1p3'],
                stdout=-1, stderr=-1
            )
        ]
        assert mock_os_system.call_args_list == [
            call('/usr/sbin/growpart /dev/nvme0n1 3'),
            call('xfs_growfs /')
        ]

    @patch('subprocess.Popen')
    @patch('syslog.syslog')
    def test_rootgrow_main_raises(self, mock_syslog, mock_subprocess_popen):
        mock_subprocess_popen.side_effect = Exception('error')
        main()
        mock_syslog.assert_called_once_with(
            syslog.LOG_ERR, 'rootgrow failed with: error'
        )

    @patch('subprocess.Popen')
    def test_get_root_device_error(self, mock_subprocess_popen):
        findmnt_mnt = Mock()
        mock_subprocess_popen.return_value = findmnt_mnt
        findmnt_mnt.communicate.return_value = (b'', b'error')
        with raises(Exception):
            get_root_device()

    @patch('subprocess.Popen')
    def test_get_root_device_root_in_snap(self, mock_subprocess_popen):
        findmnt_mnt = Mock()
        mock_subprocess_popen.return_value = findmnt_mnt
        findmnt_mnt.communicate.return_value = (
            b'/dev/sda3[/@/.snapshots/1/snapshot]',
            b''
        )
        assert get_root_device() == '/dev/sda3'

    @patch('subprocess.Popen')
    def test_get_root_device_root_on_part(self, mock_subprocess_popen):
        findmnt_mnt = Mock()
        mock_subprocess_popen.return_value = findmnt_mnt
        findmnt_mnt.communicate.return_value = (
            b'/dev/sda1',
            b''
        )
        assert get_root_device() == '/dev/sda1'

    @patch('subprocess.Popen')
    def test_get_root_filesystem_type_error(self, mock_subprocess_popen):
        root_fs = Mock()
        mock_subprocess_popen.return_value = root_fs
        root_fs.communicate.return_value = (b'ext4', b'')
        assert get_root_filesystem_type('/dev/foo') == 'ext4'
        root_fs.communicate.return_value = (b'', b'error')
        with raises(Exception):
            get_root_filesystem_type('/dev/foo')

    @patch('subprocess.Popen')
    def test_disk_device_from_root_error(self, mock_subprocess_popen):
        device = Mock()
        mock_subprocess_popen.return_value = device
        device.communicate.return_value = (b'/dev/sda', b'')
        assert get_disk_device_from_root('/dev/sda1') == '/dev/sda'
        device.communicate.return_value = (b'', b'error')
        with raises(Exception):
            get_disk_device_from_root('/dev/sda1')

    def test_get_partition_id_from_root(self):
        assert get_partition_id_from_root('/dev/sda10') == 10
        assert get_partition_id_from_root('/dev/nvme0n1p3') == 3
