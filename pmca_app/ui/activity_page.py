from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLineEdit, QPlainTextEdit, QPushButton, QWidget)

from .widgets import page_layout, title

RETAINED_LINES = 5000
ERROR_WORDS = ('error', 'traceback', 'failed', 'exception')


class ActivityPage(QWidget):
 def __init__(self, window):
  QWidget.__init__(self)
  self.window_ = window
  self.lines = []
  layout = page_layout(self)
  top = QHBoxLayout()
  top.setSpacing(8)
  top.addWidget(title('Activity'), 1)
  self.filter = QLineEdit()
  self.filter.setPlaceholderText('Filter')
  self.filter.setClearButtonEnabled(True)
  self.filter.setMaximumWidth(200)
  self.filter.textChanged.connect(self.rebuild)
  top.addWidget(self.filter)
  self.level = QComboBox()
  self.level.addItems(['All', 'Errors'])
  self.level.currentIndexChanged.connect(self.rebuild)
  top.addWidget(self.level)
  for label, handler in (('Copy', self.copy), ('Save…', self.save), ('Clear', self.clear)):
   button = QPushButton(label)
   button.clicked.connect(handler)
   top.addWidget(button)
  layout.addLayout(top)
  layout.addSpacing(14)
  self.view = QPlainTextEdit()
  self.view.setReadOnly(True)
  self.view.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
  self.view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
  self.view.setMaximumBlockCount(RETAINED_LINES)
  layout.addWidget(self.view, 1)

 def _visible(self, line):
  needle = self.filter.text().strip().lower()
  if needle and needle not in line.lower():
   return False
  return self.level.currentIndex() == 0 or any(word in line.lower() for word in ERROR_WORDS)

 def add(self, line):
  self.lines.append(line)
  if len(self.lines) > RETAINED_LINES:
   del self.lines[0]
  if self._visible(line):
   self.view.appendPlainText(line)

 def rebuild(self, *_):
  self.view.setPlainText('\n'.join(l for l in self.lines if self._visible(l)))

 def text(self):
  return self.view.toPlainText()

 def copy(self):
  QGuiApplication.clipboard().setText(self.text())

 def save(self):
  path, _ = QFileDialog.getSaveFileName(self.window_, 'Save log', 'sony-open-pmca.log', 'Text (*.txt *.log)')
  if path:
   with open(path, 'w', encoding='utf-8') as f:
    f.write(self.text() + '\n')

 def clear(self):
  self.lines = []
  self.view.clear()
