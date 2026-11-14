import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .. import state as st
from .widgets import Rows, heading, muted, page_layout, styled, title
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFont


class CameraPage(QWidget):
 def __init__(self, window):
  QWidget.__init__(self)
  self.window_ = window
  self.state = st.NO_CAMERA
  self.props = None
  self.loading = False

  outer = QVBoxLayout(self)
  outer.setContentsMargins(0, 0, 0, 0)
  scroll = QScrollArea()
  scroll.setWidgetResizable(True)
  scroll.setFrameShape(QScrollArea.Shape.NoFrame)
  outer.addWidget(scroll)
  self.body = QWidget()
  scroll.setWidget(self.body)
  self.layout_ = page_layout(self.body)
  self.render()

 def set_state(self, state):
  self.state = state
  if not state.connected:
   self.props = None
   self.loading = False
  self.render()

 def set_details(self, props):
  self.props = props
  self.loading = False
  self.render()

 def set_loading(self, loading):
  self.loading = loading
  self.render()

 def _clear(self):
  while self.layout_.count():
   item = self.layout_.takeAt(0)
   if item.widget():
    item.widget().deleteLater()
   elif item.layout():
    self._drop(item.layout())

 def _drop(self, layout):
  while layout.count():
   item = layout.takeAt(0)
   if item.widget():
    item.widget().deleteLater()

 def render(self):
  self._clear()
  state = self.state
  if state.connected:
   self._render_connected()
  elif state.kind == 'unusable':
   self.layout_.addWidget(title(state.name))
   self.layout_.addSpacing(6)
   self.layout_.addWidget(styled(QLabel(state.reason), wrap=True))
   self.layout_.addSpacing(16)
   self.layout_.addLayout(self._buttons(refresh=False, retry=True))
  else:
   self.layout_.addWidget(title('No camera connected'))
   self.layout_.addSpacing(14)
   for number, text in enumerate(st.STEPS, 1):
    if number == 3 and sys.platform != 'darwin':
     continue
    self.layout_.addWidget(styled(QLabel('%d.  %s' % (number, text)), wrap=True))
    self.layout_.addSpacing(6)
  self.layout_.addStretch(1)

 def _buttons(self, refresh=True, retry=False):
  row = QHBoxLayout()
  row.setSpacing(8)
  if retry:
   button = QPushButton('Check again')
   button.clicked.connect(self.window_.reconnect)
   row.addWidget(button)
  if refresh:
   button = QPushButton('Refresh')
   button.setEnabled(not self.window_.busy)
   button.clicked.connect(self.window_.refresh_details)
   row.addWidget(button)
   copy = QPushButton('Copy details')
   copy.clicked.connect(self.copy_details)
   row.addWidget(copy)
  row.addStretch(1)
  return row

 def _render_connected(self):
  state, props = self.state, self.props or {}
  self.layout_.addWidget(title(props.get('Model') or state.name))
  firmware = props.get('Firmware version')
  line = []
  if firmware and not str(firmware).startswith('Unavailable'):
   line.append('Firmware %s' % firmware)
  if state.mode:
   line.append(state.mode)
  if line:
   self.layout_.addSpacing(2)
   self.layout_.addWidget(muted('  ·  '.join(line), wrap=False))
  self.layout_.addSpacing(14)
  self.layout_.addLayout(self._buttons())
  self.layout_.addSpacing(10)
  if self.loading and not self.props:
   self.layout_.addWidget(muted('Reading camera…'))
   return
  if state.kind == 'installer':
   self.layout_.addWidget(muted('The camera is in app installation mode. Details return when it is back in MTP.'))
  for name, rows in st.describe(props, state):
   self.layout_.addSpacing(22)
   self.layout_.addWidget(heading(name))
   self.layout_.addSpacing(4)
   self.layout_.addWidget(Rows(rows))

 def copy_details(self):
  lines = []
  for name, rows in st.describe(self.props or {}, self.state):
   lines.append(name)
   lines.extend('  %s: %s' % (label, value) for label, value, _ in rows)
  QGuiApplication.clipboard().setText('\n'.join(lines))
