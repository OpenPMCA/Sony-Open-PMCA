"""Blocking backend operations. Thin, Qt-free wrappers over the pmca package; run them in worker threads."""
import io
import os
import re
import tempfile

from pmca.apk import ApkParser
from pmca.appstore import catalog as store
from pmca.commands import usb as cmd
from pmca.platform.backend.senser import SenserPlatformBackend
from pmca.platform.backend.usb import UsbPlatformBackend
from pmca.platform.tweaks import TweakInterface


PACKAGE_NAME = re.compile(r'^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$')


class Backend(object):
 def __init__(self, driver=None):
  self.driver = driver or cmd.getDefaultDriverName()
  self._cache_dir = None

 # camera
 def poll(self):
  return cmd.checkCameraConnection(self.driver, quiet=True)

 def read_details(self):
  return cmd.getReadOnlyCameraInfo(self.driver)

 # store
 def load_catalog(self):
  return list(store.loadCatalog().values())

 def sync_catalog(self, force=False):
  result = store.syncCatalogMetadata(force=force)
  store.saveCatalog(result)
  return list(result.catalog.values()), result

 def download(self, app, path, progress=None, abort=None):
  return store.downloadCatalogApp(app, path, progress, abort_event=abort)

 def download_to_cache(self, app, progress=None, abort=None):
  package = str(app.get('package') or '')
  if not PACKAGE_NAME.match(package):
   raise ValueError('Invalid package name in the catalog: %r' % package)
  if self._cache_dir is None:
   self._cache_dir = tempfile.mkdtemp(prefix='sony-open-pmca-')  # unique, owner-only (0700)
  return self.download(app, os.path.join(self._cache_dir, '%s.apk' % package), progress, abort)

 # install
 @staticmethod
 def preflight_apk(path):
  """Raise ValueError unless the file is a camera-compatible APK; return (package, version)."""
  with open(path, 'rb') as f:
   data = f.read()
  apk = cmd.checkApk(io.BytesIO(data))
  return apk.getPackageName(), str(apk.getVersionName())

 def install_file(self, path, status=None):
  with open(path, 'rb') as f:
   data = f.read()
  return cmd.installCommand(driverName=self.driver, apkFile=io.BytesIO(data), statusFunc=status)

 # tools
 def has_updater_image(self, model):
  return bool(model) and cmd.getFdat(model) is not None

 def tweak_session(self, kind, present):
  """Reboot into updater ('updater') or service ('service') mode and call present(TweakInterface) while it is open."""
  def complete(device):
   platform = UsbPlatformBackend(device) if kind == 'updater' else SenserPlatformBackend(device)
   platform.start()
   try:
    tweaks = TweakInterface(platform)
    if next(tweaks.getTweaks(), None):
     present(tweaks)
    else:
     print('No tweaks available')
   finally:
    platform.stop()
  (cmd.updaterShellCommand if kind == 'updater' else cmd.senserShellCommand)(complete=complete)

 def firmware_update(self, path):
  with open(path, 'rb') as f:
   cmd.firmwareUpdateCommand(f)
