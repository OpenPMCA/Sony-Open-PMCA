"""Small building blocks. Palette-driven so light and dark follow the system."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


def styled(label, size=0, weight=QFont.Weight.Normal, muted=False, wrap=False, selectable=False):
 font = label.font()
 if size:
  font.setPointSizeF(font.pointSizeF() + size)
 font.setWeight(weight)
 label.setFont(font)
 if muted:
  label.setForegroundRole(QPalette.ColorRole.PlaceholderText)
 label.setWordWrap(wrap)
 if selectable:
  label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
 return label


def title(text):
 return styled(QLabel(text), size=8, weight=QFont.Weight.DemiBold)


def heading(text):
 return styled(QLabel(text), size=1, weight=QFont.Weight.DemiBold)


def muted(text, wrap=True):
 return styled(QLabel(text), muted=True, wrap=wrap)


class Hairline(QWidget):
 def __init__(self, parent=None):
  QWidget.__init__(self, parent)
  self.setFixedHeight(1)
  self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

 def paintEvent(self, event):
  painter = QPainter(self)
  color = QColor(self.palette().color(QPalette.ColorRole.WindowText))
  color.setAlpha(36)
  painter.fillRect(self.rect(), color)


class ElidedLabel(QLabel):
 """Single line that truncates with an ellipsis instead of forcing the window wider."""
 def __init__(self, text='', parent=None):
  QLabel.__init__(self, parent)
  self._full = text
  self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
  self.setText(text)

 def setText(self, text):
  self._full = text
  self.setToolTip(text)
  self._elide()

 def resizeEvent(self, event):
  QLabel.resizeEvent(self, event)
  self._elide()

 def _elide(self):
  shown = QFontMetrics(self.font()).elidedText(self._full, Qt.TextElideMode.ElideRight, max(self.width(), 10))
  QLabel.setText(self, shown)


class StatusDot(QWidget):
 COLORS = {'ok': '#2FB344', 'warn': '#E8A317', 'off': '#8E8E93'}

 def __init__(self, parent=None):
  QWidget.__init__(self, parent)
  self.setFixedSize(10, 10)
  self._color = QColor(self.COLORS['off'])

 def set_kind(self, kind):
  self._color = QColor(self.COLORS[kind])
  self.update()

 def paintEvent(self, event):
  painter = QPainter(self)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(self._color)
  painter.drawEllipse(QRectF(1, 1, 8, 8))


class Rows(QWidget):
 """Label/value rows separated by hairlines. Values are selectable; a note sits under the value."""
 def __init__(self, rows, parent=None):
  QWidget.__init__(self, parent)
  grid = QGridLayout(self)
  grid.setContentsMargins(0, 0, 0, 0)
  grid.setHorizontalSpacing(24)
  grid.setVerticalSpacing(0)
  grid.setColumnMinimumWidth(0, 130)
  grid.setColumnStretch(1, 1)
  line = 0
  for label, value, note in rows:
   if line:
    grid.addWidget(Hairline(), line, 0, 1, 2)
    line += 1
   name = styled(QLabel(label), muted=True)
   name.setContentsMargins(0, 9, 0, 9)
   name.setAlignment(Qt.AlignmentFlag.AlignTop)
   cell = QWidget()
   box = QVBoxLayout(cell)
   box.setContentsMargins(0, 9, 0, 9)
   box.setSpacing(2)
   box.addWidget(styled(QLabel(value), wrap=True, selectable=True))
   if note:
    box.addWidget(styled(QLabel(note), size=-1, muted=True, wrap=True))
   grid.addWidget(name, line, 0, Qt.AlignmentFlag.AlignTop)
   grid.addWidget(cell, line, 1)
   line += 1


def page_layout(widget, scroll=False):
 """Standard page margins. Returns the layout to fill."""
 layout = QVBoxLayout(widget)
 layout.setContentsMargins(36, 28, 36, 24)
 layout.setSpacing(0)
 return layout


def row_layout(*widgets, stretch_first=True):
 box = QHBoxLayout()
 box.setContentsMargins(0, 0, 0, 0)
 box.setSpacing(8)
 for index, item in enumerate(widgets):
  box.addWidget(item, 1 if (stretch_first and index == 0) else 0)
 return box
