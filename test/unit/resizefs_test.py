from mock import (
    patch, Mock, call
)

from rootgrow.resizefs import resize_fs


class TestResizeFs(object):
    @patch('os.system')
    def test_resize_fs_ext(self, mock_os_system):
        resize_fs('ext3', '/dev/device')
        mock_os_system.assert_called_once_with(
            'resize2fs /dev/device'
        )

    @patch('os.system')
    @patch('subprocess.run')
    def test_resize_fs_xfs(self, mock_subprocess_run, mock_os_system):
        findmnt = Mock()
        findmnt.stdout = b'/mount/point'
        mock_subprocess_run.return_value = findmnt
        resize_fs('xfs', '/dev/device')
        mock_subprocess_run.assert_called_once_with(
            ['findmnt', '-n', '-f', '-o', 'TARGET', '/dev/device'], stdout=-1
        )
        mock_os_system.assert_called_once_with(
            'xfs_growfs /mount/point'
        )

    @patch('os.system')
    @patch('subprocess.run')
    def test_resize_fs_btrfs(self, mock_subprocess_run, mock_os_system):
        findmnt = Mock()
        findmnt.stdout = b'/mount/point'
        mock_subprocess_run.return_value = findmnt
        resize_fs('btrfs', '/dev/device')
        assert mock_subprocess_run.call_args_list == [
            call(
                ['findmnt', '-n', '-f', '-o', 'TARGET', '/dev/device'],
                stdout=-1
            ),
            call(
                ['findmnt', '-n', '-f', '-o', 'OPTIONS', '/dev/device'],
                stdout=-1
            )
        ]
        mock_os_system.assert_called_once_with(
            'btrfs filesystem resize max /mount/point'
        )

    @patch('os.system')
    @patch('subprocess.run')
    @patch('os.path.isdir')
    def test_resize_fs_btrfs_ro(
        self, mock_os_path_isdir, mock_subprocess_run, mock_os_system
    ):
        mock_os_path_isdir.return_value = True
        findmnt_mnt = Mock()
        findmnt_mnt.stdout = b'/mount/point'
        findmnt_opt = Mock()
        findmnt_opt.stdout = b'ro,foo,bar'
        mock_subprocess_run.side_effect = [findmnt_mnt, findmnt_opt]
        resize_fs('btrfs', '/dev/device')
        mock_os_system.assert_called_once_with(
            'btrfs filesystem resize max /mount/point/.snapshots'
        )

    @patch('os.system')
    @patch('subprocess.run')
    @patch('os.path.isdir')
    def test_resize_fs_btrfs_ro_no_snapshots(
        self, mock_os_path_isdir, mock_subprocess_run, mock_os_system
    ):
        mock_os_path_isdir.return_value = False
        findmnt_mnt = Mock()
        findmnt_mnt.stdout = b'/mount/point'
        findmnt_opt = Mock()
        findmnt_opt.stdout = b'ro,foo,bar'
        mock_subprocess_run.side_effect = [findmnt_mnt, findmnt_opt]
        resize_fs('btrfs', '/dev/device')
        assert not mock_os_system.called
