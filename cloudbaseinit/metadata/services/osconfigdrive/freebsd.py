from cloudbaseinit.metadata.services.osconfigdrive import base
from cloudbaseinit.openstack.common import log as logging
from oslo.config import cfg
import os
import contextlib
import shutil
import subprocess
import tempfile
import re

LOG = logging.getLogger(__name__)

class FreeBSDConfigDriveManager(base.BaseConfigDriveManager):

    def get_config_drive_files(self, target_path, check_raw_hhd=True,
                               check_cdrom=True, check_vfat=True):
        config_drive_found = False

        if check_vfat:
            LOG.debug('Looking for Config Drive in VFAT filesystems')
            config_drive_found = self._get_conf_drive_from_vfat(target_path)

        if not config_drive_found and check_raw_hhd:
            LOG.debug('Looking for Config Drive in raw HDDs')
            config_drive_found = self._get_conf_drive_from_raw_hdd(target_path)

        if not config_drive_found and check_cdrom:
            LOG.debug('Looking for Config Drive in cdrom drives')
            config_drive_found = self._get_conf_drive_from_cdrom_drive(target_path)

        return config_drive_found

    def _get_conf_drive_from_vfat(self, target_path):
        return False

    def _get_conf_drive_from_raw_hdd(self, target_path):
        return False

    def _get_conf_drive_from_cdrom_drive(self, target_path):
        cdrom = self._get_cdrom_device()
        if not cdrom:
            return False

        with tempdir() as tmp:
            umount = False
            cdrom_mount_point = self._get_existing_cdrom_mount(cdrom)
            if not cdrom_mount_point:
                try:
                    mountcmd = ['mount', '-o', 'ro', '-t', 'cd9660', cdrom, tmp]
                    subprocess.check_call(mountcmd)
                    umount = tmp
                    cdrom_mount_point = tmp
                except subprocess.CalledProcessError as exc:
                    LOG.debug('Failed mount of %s as %s: %s', cdrom, tmp, exc)
                    return False

            with unmounter(umount):
                shutil.copytree(cdrom_mount_point, target_path)
                return True

        return False

    def _get_cdrom_device(self):
        devices = self._get_devices()
        cdrom_drives = ['/dev/%s' % d for d in devices if self._is_cdrom(d)]
        if len(cdrom_drives):
            return cdrom_drives[0]
        return None

    def _get_devices(self):
        devices = []
        cmd = 'sysctl -n kern.disks'
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            devices = output.split()
        except subprocess.CalledProcessError:
            pass

        return devices

    def _is_cdrom(self, device):
        cmd = 'glabel status -s %s' % device
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            return output.startswith('iso9660/config-2')
        except subprocess.CalledProcessError:
            return False

    def _get_existing_cdrom_mount(self, device):
        existing_mounts = self._get_mounts()
        mount = None
        if device in existing_mounts:
            mount = existing_mounts[os.path.realpath(device)]['mountpoint']
        return mount

    def _get_mounts(self):
        mounts = {}
        mountre = r'^(/dev/[\S]+) on (/.*) \((.+), .+, (.+)\)$'
        cmd_output = subprocess.check_output('mount', stderr=subprocess.STDOUT, shell=True)
        mount_info = cmd_output.split('\n')
        for mount in mount_info:
            try:
                m = re.search(mountre, mount)
                dev = m.group(1)
                mp = m.group(2)
                fstype = m.group(3)
                opts = m.group(4)
            except:
                continue

            mounts[dev] = {
                'fstype': fstype,
                'mountpoint': mp,
                'opts': opts
            }

        return mounts


@contextlib.contextmanager
def tempdir(**kwargs):
    tdir = tempfile.mkdtemp(**kwargs)
    try:
        yield tdir
    finally:
        shutil.rmtree(tdir)


@contextlib.contextmanager
def unmounter(umount):
    try:
        yield umount
    finally:
        if umount:
            umount_cmd = ["umount", umount]
            subprocess.check_call(umount_cmd)
