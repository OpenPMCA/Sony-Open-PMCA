import os
import threading

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

from .runtime import run_job
from .widgets import Hairline, muted, page_layout, styled, title

UPDATER_CONFIRM = ('Restart the camera into firmware update mode to change hidden settings?\n\n'
                   'Follow the prompts on the camera and keep power and USB connected. The installed firmware is not modified. '
                   'This path has not been verified on physical hardware in this project.')
SERVICE_CONFIRM = ('Switch the camera into service mode to change hidden settings?\n\n'
                   'Service mode needs a libusb-accessible Mass Storage connection. Keep power and USB connected. '
                   'This path has not been verified on physical hardware in this project.')
FIRMWARE_CONFIRM = ('Write %s to the connected camera?\n\nThis rewrites the camera firmware. Keep power and USB connected '
                    'until the camera finishes. This path has not been verified on physical hardware in this project.')


class TweakDialog(QDialog):
 def __init__(self, tweaks, parent=None):
  QDialog.__init__(self, parent)
  self.tweaks = tweaks
  self.setWindowTitle('Hidden settings')
  self.setMinimumWidth(460)
  self.layout_ = QVBoxLayout(self)
  self.boxes = QVBoxLayout()
  self.boxes.setSpacing(10)
  self.layout_.addLayout(self.boxes)
  self.layout_.addSpacing(14)
  row = QHBoxLayout()
  row.addStretch(1)
  close = QPushButton('Close')
  close.clicked.connect(self.reject)
  self.apply = QPushButton('Apply')
  self.apply.setDefault(True)
  self.apply.clicked.connect(self.apply_all)
  row.addWidget(close)
  row.addWidget(self.apply)
  self.layout_.addLayout(row)
  self.populate()

 def populate(self):
  while self.boxes.count():
   item = self.boxes.takeAt(0)
   if item.widget():
    item.widget().deleteLater()
  for tweak_id, description, status, value in self.tweaks.getTweaks():
   box = QCheckBox('%s\n%s' % (description, value))
   box.setChecked(bool(status))
   box.toggled.connect(lambda checked, t=tweak_id: self.toggle(t, checked))
   self.boxes.addWidget(box)

 def toggle(self, tweak_id, checked):
  self.tweaks.setEnabled(tweak_id, checked)
  self.populate()

 def apply_all(self):
  self.apply.setEnabled(False)
  print('Applying tweaks...')
  run_job(lambda emit: self.tweaks.apply(), lambda _: self.accept(), self._failed)

 def _failed(self, error):
  self.apply.setEnabled(True)
  QMessageBox.warning(self, 'Could not apply', str(error))


class ToolRow(QWidget):
 def __init__(self, name, detail, buttons):
  QWidget.__init__(self)
  outer = QVBoxLayout(self)
  outer.setContentsMargins(0, 0, 0, 0)
  outer.setSpacing(0)
  outer.addWidget(Hairline())
  row = QHBoxLayout()
  row.setContentsMargins(0, 12, 0, 12)
  row.setSpacing(8)
  text = QVBoxLayout()
  text.setSpacing(2)
  text.addWidget(styled(QLabel(name), weight=QFont.Weight.DemiBold))
  self.detail = styled(QLabel(detail), muted=True, wrap=True)
  text.addWidget(self.detail)
  row.addLayout(text, 1)
  self.buttons = buttons
  for button in buttons:
   row.addWidget(button)
  outer.addLayout(row)


class ToolsPage(QWidget):
 tweaks_ready = Signal(object, object)

 def __init__(self, window):
  QWidget.__init__(self)
  self.window_ = window
  self.firmware_path = ''
  self.tweaks_ready.connect(self._show_tweaks)
  layout = page_layout(self)
  layout.addWidget(title('Tools'))
  layout.addSpacing(2)
  self.support = muted('No camera detected.', wrap=False)
  layout.addWidget(self.support)
  layout.addSpacing(16)

  self.updater = QPushButton('Start…')
  self.updater.clicked.connect(lambda: self.start_tweaks('updater', UPDATER_CONFIRM))
  self.service = QPushButton('Start…')
  self.service.clicked.connect(lambda: self.start_tweaks('service', SERVICE_CONFIRM))
  choose = QPushButton('Choose file…')
  choose.clicked.connect(self.choose_firmware)
  self.flash = QPushButton('Update…')
  self.flash.clicked.connect(self.update_firmware)
  self.firmware_row = ToolRow('Firmware update', 'No file chosen.', [choose, self.flash])
  self.choose = choose
  layout.addWidget(ToolRow('Updater mode', 'Restarts the camera into firmware update mode to change hidden settings. Firmware stays untouched.', [self.updater]))
  layout.addWidget(ToolRow('Service mode', 'Uses the service USB mode. Needs libusb access to the camera in Mass Storage.', [self.service]))
  layout.addWidget(self.firmware_row)
  layout.addWidget(Hairline())
  layout.addStretch(1)
  self.refresh_controls()

 def update_camera(self, state):
  if not state.connected and state.kind != 'unusable':
   self.support.setText('No camera detected.')
  else:
   has = self.window_.backend.has_updater_image(state.name) if state.name else False
   self.support.setText('%s: %s' % (state.name, 'updater image available' if has else 'no updater image for this model'))

 def refresh_controls(self):
  free = not self.window_.busy
  for button in (self.updater, self.service, self.choose):
   button.setEnabled(free)
  self.flash.setEnabled(free and bool(self.firmware_path))

 def choose_firmware(self):
  path, _ = QFileDialog.getOpenFileName(self.window_, 'Choose a firmware file', os.path.expanduser('~/Downloads'), 'Firmware (*.dat);;All files (*)')
  if path:
   self.firmware_path = path
   self.firmware_row.detail.setText(os.path.basename(path))
   self.refresh_controls()

 def _ask(self, title_text, message):
  return QMessageBox.question(self.window_, title_text, message, QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Ok

 def start_tweaks(self, kind, confirm):
  if not self._ask('Start %s mode' % kind, confirm) or not self.window_.begin_operation():
   return
  backend = self.window_.backend

  def present(tweaks):
   done = threading.Event()
   self.tweaks_ready.emit(tweaks, done)
   done.wait()

  self._run(lambda emit: backend.tweak_session(kind, present))

 def _show_tweaks(self, tweaks, done):
  try:
   TweakDialog(tweaks, self.window_).exec()
  finally:
   done.set()

 def update_firmware(self):
  path = self.firmware_path
  if not path or not os.path.isfile(path) or not self._ask('Update firmware', FIRMWARE_CONFIRM % os.path.basename(path)):
   return
  if not self.window_.begin_operation():
   return
  backend = self.window_.backend
  self._run(lambda emit: backend.firmware_update(path))

 def _run(self, work):
  def done(_):
   self.window_.end_operation()

  def failed(error):
   self.window_.end_operation()
   print('Error: %s' % error)
   QMessageBox.warning(self.window_, 'Operation failed', str(error))

  run_job(work, done, failed)
