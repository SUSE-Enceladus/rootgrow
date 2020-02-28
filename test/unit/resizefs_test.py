import unittest
from pytest import raises
from mock import (
    patch, Mock, call
)

from rootgrow.resizefs import (
    get_mount_point, get_mount_options, resize_fs
)


class TestResizeFs(unittest.TestCase):
    @patch('os.system')
    def test_resize_fs_ext(self, mock_os_system):
        resize_fs('ext3', '/dev/device')
        mock_os_system.assert_called_once_with(
            'resize2fs /dev/device'
        )

    @patch('os.system')
    @patch('subprocess.Popen')
    def test_resize_fs_xfs(self, mock_subprocess_popen, mock_os_system):
        findmnt = Mock()
        attrs = {'communicate.return_value': (b'/mount/point', b'')}
        findmnt.configure_mock(**attrs)
        mock_subprocess_popen.return_value = findmnt
        resize_fs('xfs', '/dev/device')
        mock_subprocess_popen.assert_called_once_with(
            ['findmnt', '-n', '-f', '-o', 'TARGET', '/dev/device'],
            stdout=-1, stderr=-1
        )
        mock_os_system.assert_called_once_with(
            'xfs_growfs /mount/point'
        )

    @patch('os.system')
    @patch('subprocess.Popen')
    def test_resize_fs_btrfs(self, mock_subprocess_popen, mock_os_system):
        findmnt = Mock()
        attrs = {'communicate.return_value': (b'/mount/point', b'')}
        findmnt.configure_mock(**attrs)
        mock_subprocess_popen.return_value = findmnt
        resize_fs('btrfs', '/dev/device')
        assert mock_subprocess_popen.call_args_list == [
            call(
                ['findmnt', '-n', '-f', '-o', 'TARGET', '/dev/device'],
                stdout=-1, stderr=-1
            ),
            call(
                ['findmnt', '-n', '-f', '-o', 'OPTIONS', '/dev/device'],
                stdout=-1, stderr=-1
            )
        ]
        mock_os_system.assert_called_once_with(
            'btrfs filesystem resize max /mount/point'
        )

    @patch('os.system')
    @patch('subprocess.Popen')
    @patch('os.path.isdir')
    def test_resize_fs_btrfs_ro(
        self, mock_os_path_isdir, mock_subprocess_popen, mock_os_system
    ):
        mock_os_path_isdir.return_value = True
        findmnt_mnt = Mock()
        attrs = {'communicate.return_value': (b'/mount/point', b'')}
        findmnt_mnt.configure_mock(**attrs)
        findmnt_opt = Mock()
        attrs = {'communicate.return_value': (b'ro,foo,bar', b'')}
        findmnt_opt.configure_mock(**attrs)
        mock_subprocess_popen.side_effect = [findmnt_mnt, findmnt_opt]
        resize_fs('btrfs', '/dev/device')
        mock_os_system.assert_called_once_with(
            'btrfs filesystem resize max /mount/point/.snapshots'
        )

    @patch('os.system')
    @patch('subprocess.Popen')
    @patch('os.path.isdir')
    def test_resize_fs_btrfs_ro_no_snapshots(
        self, mock_os_path_isdir, mock_subprocess_popen, mock_os_system
    ):
        mock_os_path_isdir.return_value = False
        findmnt_mnt = Mock()
        attrs = {'communicate.return_value': (b'/mount/point', b'')}
        findmnt_mnt.configure_mock(**attrs)
        findmnt_opt = Mock()
        attrs = {'communicate.return_value': (b'ro,foo,bar', b'')}
        findmnt_opt.configure_mock(**attrs)
        mock_subprocess_popen.side_effect = [findmnt_mnt, findmnt_opt]
        resize_fs('btrfs', '/dev/device')
        assert not mock_os_system.called

    @patch('subprocess.Popen')
    def test_get_mount_point_error(self, mock_subprocess_popen):
        findmnt_mnt = Mock()
        mock_subprocess_popen.return_value = findmnt_mnt
        findmnt_mnt.communicate.return_value = (b'', b'error')
        with raises(Exception):
            get_mount_point('/foo')

    @patch('subprocess.Popen')
    def test_get_mount_options_error(self, mock_subprocess_popen):
        findmnt_mnt = Mock()
        mock_subprocess_popen.return_value = findmnt_mnt
        findmnt_mnt.communicate.return_value = (b'', b'error')
        with raises(Exception):
            get_mount_options('/foo')
