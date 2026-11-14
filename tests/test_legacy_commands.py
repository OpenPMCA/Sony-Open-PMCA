import io
import threading
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from pmca.commands import usb as cmd

LEGACY = ('firmwareUpdateCommand', 'updaterShellCommand', 'senserShellCommand',
          'guessFirmwareCommand', 'gpsUpdateCommand', 'streamingCommand', 'wifiCommand')


class LegacyCommandsTest(unittest.TestCase):
 def test_console_and_gui_entry_points_exist(self):
  for name in LEGACY:
   self.assertTrue(callable(getattr(cmd, name, None)), name)

 def test_bundled_updater_images_cover_pre_pmca_and_first_gen_bodies(self):
  for model in ('ILCE-7', 'NEX-5R', 'NEX-6', 'NEX-5', 'NEX-7', 'SLT-A57', 'DSC-HX60V'):
   self.assertIsNotNone(cmd.getFdat(model), model)
  self.assertIsNone(cmd.getFdat('ILCE-9'))

 def test_updater_shell_holds_busy_flag_and_releases_it(self):
  seen = []
  device = MagicMock(spec=cmd.SonyMtpExtCmdDevice)
  driver = MagicMock()
  driver.__enter__.return_value = driver
  with patch.object(cmd, 'importDriver', return_value=driver), \
       patch.object(cmd, 'getDevice', side_effect=lambda d: seen.append(cmd.is_camera_busy()) or device), \
       patch.object(cmd, 'SonyExtCmdCamera') as camera:
   camera.return_value.getCameraInfo.return_value.modelName = 'ILCE-9'
   out = io.StringIO()
   with redirect_stdout(out):
    cmd.updaterShellCommand()
  self.assertEqual(seen, [True])
  self.assertFalse(cmd.is_camera_busy())
  self.assertIn('does not support custom firmware updates', out.getvalue())

 def test_second_mode_switch_is_refused_while_camera_is_busy(self):
  errors = []
  def attempt():
   try:
    cmd.senserShellCommand()
   except cmd.CameraBusyException as e:
    errors.append(e)
  with patch.object(cmd, 'importDriver', side_effect=AssertionError('USB touched')):
   with cmd.camera_operation():
    t = threading.Thread(target=attempt)
    t.start()
    t.join()
  self.assertEqual(len(errors), 1)
  self.assertFalse(cmd.is_camera_busy())


if __name__ == '__main__':
 unittest.main()
