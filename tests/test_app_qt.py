import os
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from pmca_app.ui.runtime import LogBus
from pmca_app.ui.window import MainWindow

APPS = [
 {'package': 'a.b.one', 'name': 'One', 'author': 'x', 'desc': 'first', 'version': '1.0', 'featured': True},
 {'package': 'a.b.two', 'name': 'Two', 'author': 'y', 'desc': 'second', 'version': '2.0'},
]
READY = {'appConnected': True, 'name': 'ILCE-7', 'mode': 'MTP', 'serial': '1', 'app_installation_supported': True}


class FakeBackend(object):
 def __init__(self):
  self.installed = []
  self.fail = None

 def poll(self):
  return None

 def load_catalog(self):
  return list(APPS)

 def sync_catalog(self, force=False):
  return list(APPS), SimpleNamespace(success=True, errors=[])

 def read_details(self):
  return {'Model': 'ILCE-7', 'Serial number': '1', 'USB mode': 'MTP'}

 def download_to_cache(self, app, progress=None, abort=None):
  progress(5, 10)
  return {'path': '/tmp/%s.apk' % app['package']}

 def install_file(self, path, status=None):
  if self.fail:
   raise self.fail
  status(SimpleNamespace(percent=50, message='halfway'))
  self.installed.append(path)
  return SimpleNamespace(code=0, message='ok')

 def has_updater_image(self, model):
  return model == 'ILCE-7'

 @staticmethod
 def preflight_apk(path):
  return 'a.b.one', '1.0'


def wait_for(condition, timeout=5.0):
 end = time.time() + timeout
 while time.time() < end:
  QCoreApplication.processEvents()
  if condition():
   return True
  time.sleep(0.01)
 return False


class AppQtTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.app = QApplication.instance() or QApplication([])

 def setUp(self):
  self.backend = FakeBackend()
  self.window = MainWindow(self.backend, '1.2.0')
  self.addCleanup(self.window.deleteLater)

 def test_starts_on_camera_with_connection_steps(self):
  self.assertEqual(self.window.nav.currentRow(), 0)
  self.assertEqual(self.window.status_text.text(), 'No camera')
  self.assertFalse(self.window.apps_page.rows[0].install.isEnabled())

 def test_ready_camera_loads_details_and_enables_install(self):
  self.window.on_status(READY)
  self.assertTrue(wait_for(lambda: self.window.camera_page.props))
  self.assertEqual(self.window.status_text.text(), 'ILCE-7 · MTP')
  self.assertTrue(all(row.install.isEnabled() for row in self.window.apps_page.rows))
  self.assertTrue(self.window.tools_page.support.text().endswith('updater image available'))

 def test_catalog_is_listed_featured_first_and_filterable(self):
  names = [r.app['name'] for r in self.window.apps_page.rows]
  self.assertEqual(names, ['One', 'Two'])
  self.window.apps_page.filter.setText('second')
  self.assertEqual([r.isHidden() for r in self.window.apps_page.rows], [True, False])

 def test_one_click_install_downloads_installs_and_reports(self):
  self.window.on_status(READY)
  page = self.window.apps_page
  with patch.object(type(page), '_confirm', return_value=True):
   page.install_app(APPS[0])
  self.assertTrue(self.window.busy)
  self.assertTrue(wait_for(lambda: not self.window.busy))
  self.assertEqual(self.backend.installed, ['/tmp/a.b.one.apk'])
  self.assertIn('Installed on ILCE-7', page.message.toolTip())

 def test_declined_confirmation_touches_nothing(self):
  self.window.on_status(READY)
  with patch.object(type(self.window.apps_page), '_confirm', return_value=False):
   self.window.apps_page.install_app(APPS[0])
  self.assertFalse(self.window.busy)
  self.assertEqual(self.backend.installed, [])

 def test_unknown_outcome_is_reported_not_hidden(self):
  self.window.on_status(READY)
  self.backend.fail = SimpleNamespace(outcome_unknown=True)
  error = RuntimeError('link dropped')
  error.outcome_unknown = True
  self.backend.fail = error
  shown = []
  page = self.window.apps_page
  with patch.object(type(page), '_confirm', return_value=True), \
       patch.object(QMessageBox, 'warning', lambda *a: shown.append(a[2])):
   page.install_app(APPS[1])
   self.assertTrue(wait_for(lambda: shown))
  self.assertIn('outcome is unknown', shown[0])
  self.assertFalse(self.window.busy)

 def test_only_one_operation_at_a_time_and_close_is_blocked(self):
  self.assertTrue(self.window.begin_operation())
  self.assertFalse(self.window.begin_operation())
  with patch.object(QMessageBox, 'information') as info:
   self.assertFalse(self.window.close())
  info.assert_called_once()
  self.window.end_operation()

 def test_activity_collects_lines_and_filters_errors(self):
  bus = LogBus()
  bus.line.connect(self.window.activity_page.add)
  bus.write('Camera connected\nError: link dropped\npartial')
  self.assertEqual(self.window.activity_page.text(), 'Camera connected\nError: link dropped')
  self.window.activity_page.level.setCurrentIndex(1)
  self.assertEqual(self.window.activity_page.text(), 'Error: link dropped')

 def test_shortcuts_target_four_pages(self):
  self.assertEqual(self.window.stack.count(), 4)
  self.window.nav.setCurrentRow(3)
  self.assertIs(self.window.stack.currentWidget(), self.window.tools_page)


if __name__ == '__main__':
 unittest.main()
