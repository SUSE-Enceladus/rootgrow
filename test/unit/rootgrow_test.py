import syslog
from mock import (
    patch, Mock, call
)

from rootgrow.rootgrow import main


class TestRootGrow(object):
    @patch('os.system')
    @patch('subprocess.run')
    def test_rootgrow_main(self, mock_subprocess_run, mock_os_system):
        root_device = Mock()
        root_device.stdout = b'/dev/sda3'
        root_fs = Mock()
        root_fs.stdout = b'ext3'
        root_disk = Mock()
        root_disk.stdout = b'/dev/sda3 part\n/dev/sda disk'
        root_part = Mock()
        root_part.stdout = \
            b'/dev/sda\n/dev/sda1\n/dev/sda2\n/dev/sda3\n/dev/sda4'
        mock_subprocess_run.side_effect = [
            root_device, root_fs, root_disk, root_part
        ]
        main()
        assert mock_subprocess_run.call_args_list == [
            call(
                ['findmnt', '-n', '-f', '-o', 'SOURCE', '/'],
                stdout=-1
            ),
            call(
                ['blkid', '-s', 'TYPE', '-o', 'value', '/dev/sda3'],
                stdout=-1
            ),
            call(
                [
                    'lsblk', '-p', '-n', '-r', '-s', '-o',
                    'NAME,TYPE', '/dev/sda3'
                ],
                stdout=-1
            ),
            call(
                ['lsblk', '-p', '-n', '-r', '-o', 'NAME', '/dev/sda'],
                stdout=-1
            )
        ]
        assert mock_os_system.call_args_list == [
            call('/usr/sbin/growpart /dev/sda 3'),
            call('resize2fs /dev/sda3')
        ]

    @patch('subprocess.run')
    @patch('syslog.syslog')
    def test_rootgrow_main_raises(self, mock_syslog, mock_subprocess_run):
        mock_subprocess_run.side_effect = Exception('error')
        main()
        mock_syslog.assert_called_once_with(
            syslog.LOG_ERR, 'rootgrow failed with: error'
        )
