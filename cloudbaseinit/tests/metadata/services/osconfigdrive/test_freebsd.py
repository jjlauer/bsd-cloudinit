import importlib
import os
import unittest

try:
    import unittest.mock as mock
except ImportError:
    import mock
from oslo.config import cfg

from cloudbaseinit import exception
from cloudbaseinit.tests import testutils


CONF = cfg.CONF


class TestFreeBSDConfigDriveManager(unittest.TestCase):

    def setUp(self):
        self.freebsd = importlib.import_module(
            "cloudbaseinit.metadata.services.osconfigdrive.freebsd")

        self._config_manager = self.freebsd.FreeBSDConfigDriveManager()

    def test_get_config_drive_files_default(self):
        response = self._config_manager.get_config_drive_files('fake_path')
        self.assertFalse(response)

    def test_get_config_drive_files_vfat(self):
        target = mock.MagicMock()
        with mock.patch.object(self._config_manager, '_get_conf_drive_from_vfat') as cm:
            response = self._config_manager.get_config_drive_files(target)
        cm.assert_called_once_with(target)

    def test_get_config_drive_files_vfat_returned(self):
        target = mock.MagicMock()
        with mock.patch.object(self._config_manager, '_get_conf_drive_from_vfat') as cm:
            response = self._config_manager.get_config_drive_files(target)
        self.assertEqual(response, cm.return_value)

    def test_get_config_drive_files_raw_hdd(self):
        target = mock.MagicMock()
        with mock.patch.object(self._config_manager, '_get_conf_drive_from_raw_hdd') as cm:
            response = self._config_manager.get_config_drive_files(target)
        cm.assert_called_once_with(target)

    def test_get_config_drive_files_raw_hdd_returned(self):
        target = mock.MagicMock()
        with mock.patch.object(self._config_manager, '_get_conf_drive_from_raw_hdd') as cm:
            response = self._config_manager.get_config_drive_files(target)
        self.assertEqual(response, cm.return_value)

    def test_get_config_drive_files_cdrom_drive(self):
        target = mock.MagicMock()
        with mock.patch.object(self._config_manager, '_get_conf_drive_from_cdrom_drive') as cm:
            response = self._config_manager.get_config_drive_files(target)
        cm.assert_called_once_with(target)

    def test_get_config_drive_files_raw_hdd_returned(self):
        target = mock.MagicMock()
        with mock.patch.object(self._config_manager, '_get_conf_drive_from_cdrom_drive') as cm:
            response = self._config_manager.get_config_drive_files(target)
        self.assertEqual(response, cm.return_value)


class TestGetConfigDriveFromCdromDrive(TestFreeBSDConfigDriveManager):

    def test_default(self):
        target = mock.MagicMock()
        response = self._config_manager._get_conf_drive_from_cdrom_drive(target)
        self.assertFalse(response)

    def test_retrieves_devices(self):
        target = mock.MagicMock()
        with mock.patch.object(self._config_manager, '_get_devices') as cm:
            response = self._config_manager._get_conf_drive_from_cdrom_drive(target)
        cm.assert_called_once_with()

    def test_get_devices(self):
        mock_output = 'cd0 vtbd0\n'
        with mock.patch('cloudbaseinit.metadata.services.osconfigdrive.freebsd.subprocess') as cm:
            cm.check_output.return_value = mock_output
            devices = self._config_manager._get_devices()

        expected_devices = ['cd0', 'vtbd0']
        self.assertEqual(devices, expected_devices)

    def test_retrieves_mounts(self):
        target = mock.MagicMock()
        mocks = {
            '_get_devices': mock.MagicMock(return_value=['cd0']),
            '_is_cdrom': mock.MagicMock(return_value=True),
            '_get_mounts': mock.MagicMock()
        }
        with mock.patch.multiple(self._config_manager, **mocks):
            response = self._config_manager._get_conf_drive_from_cdrom_drive(target)
        mocks['_get_mounts'].assert_called_once_with()

    def test_get_mounts(self):
        mount_output = (
            '/dev/vtbd0p2 on / (ufs, local, journaled soft-updates)\n'
            'devfs on /dev (devfs, local, multilabel)\n'
            '/dev/cd0 on /mnt/cdrom (cd9660, local, read-only)\n'
            'procfs on /proc (procfs, local)\n'
        )
        with mock.patch('cloudbaseinit.metadata.services.osconfigdrive.freebsd.subprocess') as cm:
            cm.check_output.return_value = mount_output
            mounts = self._config_manager._get_mounts()

        expected_mount_info = {
            '/dev/cd0': {
                'fstype': 'cd9660',
                'mountpoint': '/mnt/cdrom',
                'opts': 'read-only'
            },
            '/dev/vtbd0p2': {
                'fstype': 'ufs',
                'mountpoint': '/',
                'opts': 'journaled soft-updates'
            }
        }
        self.assertEqual(mounts, expected_mount_info)
