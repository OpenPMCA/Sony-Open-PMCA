import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
                               QStackedWidget, QVBoxLayout, QWidget)

from .. import state as st
from .activity_page import ActivityPage
from .apps_page import AppsPage
from .camera_page import CameraPage
from .runtime import CameraMonitor, run_job
from .tools_page import ToolsPage
from .widgets import StatusDot, styled

STYLE = '''
QWidget#sidebar { border-right: 1px solid palette(mid); }
QListWidget#nav { border: none; background: transparent; outline: none; }
QListWidget#nav::item { padding: 7px 12px; border-radius: 6px; margin: 1px 0; }
QListWidget#nav::item:selected { background: palette(highlight); color: palette(highlighted-text); }
'''

PAGES = ('Camera', 'Apps', 'Activity', 'Tools')


class MainWindow(QMainWindow):
 def __init__(self, backend, version='', logo=None):
  QMainWindow.__init__(self)
  self.backend = backend
  self.state = st.NO_CAMERA
  self.busy = False
  self._reading = False
  self.monitor = None
  self.setWindowTitle('Sony Open PMCA')
  self.resize(1000, 680)
  self.setMinimumSize(820, 560)
  self.setStyleSheet(STYLE)

  root = QWidget()
  self.setCentralWidget(root)
  row = QHBoxLayout(root)
  row.setContentsMargins(0, 0, 0, 0)
  row.setSpacing(0)

  side = QWidget()
  side.setObjectName('sidebar')
  side.setFixedWidth(196)
  column = QVBoxLayout(side)
  column.setContentsMargins(12, 18, 12, 14)
  column.setSpacing(0)
  brand = QHBoxLayout()
  brand.setContentsMargins(8, 0, 0, 0)
  brand.setSpacing(8)
  if logo and os.path.isfile(logo):
   mark = QLabel()
   mark.setPixmap(QPixmap(logo).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
   brand.addWidget(mark)
  brand.addWidget(styled(QLabel('Open PMCA'), weight=QFont.Weight.DemiBold))
  brand.addStretch(1)
  column.addLayout(brand)
  column.addSpacing(18)
  self.nav = QListWidget()
  self.nav.setObjectName('nav')
  self.nav.setFocusPolicy(Qt.FocusPolicy.NoFocus)
  for name in PAGES:
   self.nav.addItem(QListWidgetItem(name))
  column.addWidget(self.nav, 1)

  status = QHBoxLayout()
  status.setContentsMargins(8, 0, 0, 0)
  status.setSpacing(8)
  self.dot = StatusDot()
  self.status_text = styled(QLabel('No camera'), size=-1)
  status.addWidget(self.dot)
  status.addWidget(self.status_text, 1)
  column.addLayout(status)
  if version:
   column.addSpacing(4)
   version_label = styled(QLabel('Version %s' % version), size=-2, muted=True)
   version_label.setContentsMargins(26, 0, 0, 0)
   column.addWidget(version_label)
  row.addWidget(side)

  self.stack = QStackedWidget()
  self.camera_page = CameraPage(self)
  self.apps_page = AppsPage(self)
  self.activity_page = ActivityPage(self)
  self.tools_page = ToolsPage(self)
  for page in (self.camera_page, self.apps_page, self.activity_page, self.tools_page):
   self.stack.addWidget(page)
  row.addWidget(self.stack, 1)

  self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
  self.nav.setCurrentRow(0)
  for index in range(len(PAGES)):
   QShortcut(QKeySequence('Ctrl+%d' % (index + 1)), self, activated=lambda i=index: self.nav.setCurrentRow(i))

  self.apps_page.set_apps(self.backend.load_catalog())

 # lifecycle
 def start(self):
  self.monitor = CameraMonitor(self.backend.poll)
  self.monitor.status.connect(self.on_status)
  self.monitor.start()
  run_job(lambda emit: self.backend.sync_catalog(), lambda value: self.apps_page.set_apps(value[0]), None)

 def closeEvent(self, event):
  if self.busy:
   QMessageBox.information(self, 'Operation running', 'Wait for the camera operation to finish before closing.')
   event.ignore()
   return
  if self.monitor:
   self.monitor.stop()
  event.accept()

 # camera state
 def on_status(self, info):
  state = st.from_status(info)
  previous, self.state = self.state, state
  if state == previous:
   return
  self.camera_page.set_state(state)
  self.apps_page.refresh_controls()
  self.tools_page.update_camera(state)
  self._update_status_line()
  if state.connected and state.kind == 'ready' and (not previous.connected or previous.identity != state.identity):
   self.refresh_details()

 def _update_status_line(self):
  state = self.state
  if self.busy:
   self.dot.set_kind('warn')
   self.status_text.setText('Working…')
  elif state.kind == 'ready':
   self.dot.set_kind('ok')
   self.status_text.setText('%s · %s' % (state.name, state.mode or 'USB'))
  elif state.kind == 'installer':
   self.dot.set_kind('warn')
   self.status_text.setText('%s · installing' % state.name)
  elif state.kind == 'unusable':
   self.dot.set_kind('warn')
   self.status_text.setText('%s · not ready' % state.name)
  else:
   self.dot.set_kind('off')
   self.status_text.setText('No camera')

 def reconnect(self):
  run_job(lambda emit: self.backend.poll(), self.on_status, None)

 def refresh_details(self):
  if self._reading or self.busy or self.state.kind != 'ready':
   return
  self._reading = True
  if self.monitor:
   self.monitor.pause(True)
  self.camera_page.set_loading(True)

  def done(props):
   self._finish_reading()
   self.camera_page.set_details(props)

  def failed(error):
   self._finish_reading()
   print('Could not read camera details: %s' % error)
   self.camera_page.set_details({})

  run_job(lambda emit: self.backend.read_details(), done, failed)

 def _finish_reading(self):
  self._reading = False
  if self.monitor and not self.busy:
   self.monitor.pause(False)

 # exclusive camera operations
 def begin_operation(self):
  if self.busy:
   return False
  self.busy = True
  if self.monitor:
   self.monitor.pause(True)
  self._sync_controls()
  return True

 def end_operation(self):
  self.busy = False
  if self.monitor:
   self.monitor.pause(False)
  self._sync_controls()
  self.reconnect()

 def _sync_controls(self):
  self.apps_page.refresh_controls()
  self.tools_page.refresh_controls()
  self.camera_page.render()
  self._update_status_line()
