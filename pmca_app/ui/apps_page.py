import os
import threading

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox, QProgressBar,
                               QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget)

from pmca.util.http import DownloadCancelledError

from .runtime import run_job
from .widgets import ElidedLabel, Hairline, muted, page_layout, styled, title


def installed_message(result, camera):
 """One-line outcome of a finished installation."""
 code = getattr(result, 'code', 0)
 if code not in (0, None):
  return False, 'The camera reported: %s' % getattr(result, 'message', result)
 return True, 'Installed on %s. Check the camera’s application list.' % (camera or 'the camera')


class AppRow(QWidget):
 def __init__(self, app, page):
  QWidget.__init__(self)
  self.app = app
  outer = QVBoxLayout(self)
  outer.setContentsMargins(0, 0, 0, 0)
  outer.setSpacing(0)
  outer.addWidget(Hairline())
  row = QHBoxLayout()
  row.setContentsMargins(0, 11, 0, 11)
  row.setSpacing(12)
  text = QVBoxLayout()
  text.setSpacing(1)
  head = QHBoxLayout()
  head.setSpacing(8)
  head.addWidget(styled(QLabel(app.get('name') or app['package']), weight=QFont.Weight.DemiBold))
  if app.get('version'):
   head.addWidget(styled(QLabel(str(app['version'])), muted=True))
  head.addStretch(1)
  text.addLayout(head)
  by = ' · '.join(x for x in (app.get('author'), app.get('desc')) if x)
  line = ElidedLabel(by)
  line.setForegroundRole(line.palette().ColorRole.PlaceholderText)
  text.addWidget(line)
  row.addLayout(text, 1)
  self.install = QPushButton('Install')
  self.install.clicked.connect(lambda: page.install_app(app))
  row.addWidget(self.install)
  more = QPushButton('More')
  menu = QMenu(more)
  menu.addAction('Save APK…', lambda: page.save_app(app))
  if app.get('homepage'):
   menu.addAction('Open source page', lambda: QDesktopServices.openUrl(QUrl(app['homepage'])))
  more.setMenu(menu)
  row.addWidget(more)
  outer.addLayout(row)

 def matches(self, text):
  hay = ' '.join(str(self.app.get(k, '')) for k in ('name', 'package', 'author', 'desc')).lower()
  return text in hay


class AppsPage(QWidget):
 def __init__(self, window):
  QWidget.__init__(self)
  self.window_ = window
  self.rows = []
  self.abort = None
  layout = page_layout(self)

  top = QHBoxLayout()
  top.setSpacing(8)
  top.addWidget(title('Apps'), 1)
  self.filter = QLineEdit()
  self.filter.setPlaceholderText('Filter')
  self.filter.setClearButtonEnabled(True)
  self.filter.setMaximumWidth(200)
  self.filter.textChanged.connect(self.apply_filter)
  top.addWidget(self.filter)
  self.file_button = QPushButton('Install APK file…')
  self.file_button.clicked.connect(self.install_file)
  top.addWidget(self.file_button)
  self.sync_button = QPushButton('Check updates')
  self.sync_button.clicked.connect(self.sync)
  top.addWidget(self.sync_button)
  layout.addLayout(top)
  layout.addSpacing(16)

  scroll = QScrollArea()
  scroll.setWidgetResizable(True)
  scroll.setFrameShape(QScrollArea.Shape.NoFrame)
  self.list = QWidget()
  self.list_layout = QVBoxLayout(self.list)
  self.list_layout.setContentsMargins(0, 0, 0, 0)
  self.list_layout.setSpacing(0)
  self.list_layout.addStretch(1)
  scroll.setWidget(self.list)
  layout.addWidget(scroll, 1)

  self.strip = QWidget()
  strip = QHBoxLayout(self.strip)
  strip.setContentsMargins(0, 12, 0, 0)
  strip.setSpacing(12)
  self.message = ElidedLabel('')
  strip.addWidget(self.message, 1)
  self.bar = QProgressBar()
  self.bar.setTextVisible(False)
  self.bar.setFixedWidth(180)
  self.bar.setMaximumHeight(6)
  strip.addWidget(self.bar)
  self.cancel = QPushButton('Cancel')
  self.cancel.clicked.connect(self.cancel_download)
  strip.addWidget(self.cancel)
  layout.addWidget(self.strip)
  self.strip.hide()

 # list
 def set_apps(self, apps):
  for row in self.rows:
   row.deleteLater()
  self.rows = []
  for app in sorted(apps, key=lambda a: (not a.get('featured'), (a.get('name') or '').lower())):
   row = AppRow(app, self)
   self.rows.append(row)
   self.list_layout.insertWidget(self.list_layout.count() - 1, row)
  self.refresh_controls()

 def apply_filter(self, text):
  text = text.strip().lower()
  for row in self.rows:
   row.setVisible(row.matches(text))

 def refresh_controls(self):
  busy = self.window_.busy
  state = self.window_.state
  for row in self.rows:
   ok = state.can_install and not busy
   row.install.setEnabled(ok)
   row.install.setToolTip('' if ok or busy else (state.install_reason or 'Connect a camera in MTP mode first.'))
  self.file_button.setEnabled(state.can_install and not busy)
  self.sync_button.setEnabled(not busy)

 # operation strip
 def show_progress(self, percent, message):
  self.strip.show()
  self.message.setText(message)
  if percent is None:
   self.bar.setRange(0, 0)
  else:
   self.bar.setRange(0, 100)
   self.bar.setValue(int(percent))

 def finish(self, message):
  self.bar.setRange(0, 100)
  self.bar.setValue(0)
  self.message.setText(message)
  self.cancel.hide()
  self.strip.show()

 def cancel_download(self):
  if self.abort:
   self.abort.set()

 # actions
 def _confirm(self, name, detail):
  box = QMessageBox(self.window_)
  box.setIcon(QMessageBox.Icon.Question)
  box.setText('Install %s on %s?' % (name, self.window_.state.name or 'the camera'))
  box.setInformativeText(detail)
  install = box.addButton('Install', QMessageBox.ButtonRole.AcceptRole)
  box.addButton(QMessageBox.StandardButton.Cancel)
  box.exec()
  return box.clickedButton() is install

 def install_app(self, app):
  if not self._confirm(app.get('name') or app['package'],
                       'Check that the app supports this model and firmware. Keep the camera powered and connected until it finishes.'):
   return
  backend = self.window_.backend
  self.abort = threading.Event()
  abort = self.abort
  name = app.get('name') or app['package']

  def work(emit):
   def got(done, total):
    emit(100 * done / total if total else None, 'Downloading %s' % name)
   downloaded = backend.download_to_cache(app, got, abort)
   emit(None, 'Installing %s' % name)
   return backend.install_file(downloaded['path'], lambda s: emit(s.percent, 'Installing %s: %s' % (name, s.message)))

  self._start(work, 'Preparing %s' % name, cancellable=True)

 def install_file(self):
  path, _ = QFileDialog.getOpenFileName(self.window_, 'Choose an APK', os.path.expanduser('~/Downloads'), 'Android apps (*.apk)')
  if not path:
   return
  backend = self.window_.backend
  try:
   package, version = backend.preflight_apk(path)
  except Exception as error:
   QMessageBox.warning(self.window_, 'Cannot install this file', str(error))
   return
  if not self._confirm('%s %s' % (package, version),
                       'Check that the app supports this model and firmware. Keep the camera powered and connected until it finishes.'):
   return
  self.abort = None

  def work(emit):
   return backend.install_file(path, lambda s: emit(s.percent, 'Installing: %s' % s.message))

  self._start(work, 'Preparing %s' % os.path.basename(path), cancellable=False)

 def _start(self, work, first_message, cancellable):
  if not self.window_.begin_operation():
   return
  self.cancel.setVisible(cancellable)
  self.show_progress(None, first_message)
  run_job(work, self._installed, self._failed, lambda p, m: self.show_progress(p, m))

 def _installed(self, result):
  ok, message = installed_message(result, self.window_.state.name)
  self.finish(message)
  self.window_.end_operation()
  if not ok:
   QMessageBox.warning(self.window_, 'Installation did not complete', message)

 def _failed(self, error):
  self.window_.end_operation()
  if isinstance(error, DownloadCancelledError):
   self.finish('Download cancelled.')
   return
  unknown = getattr(error, 'outcome_unknown', False)
  message = ('The outcome is unknown. Check the camera’s application list before retrying.\n\n%s' % error) if unknown else str(error)
  self.finish('Installation failed.')
  QMessageBox.warning(self.window_, 'Installation failed', message)

 def save_app(self, app):
  name = app.get('name') or app['package']
  path, _ = QFileDialog.getSaveFileName(self.window_, 'Save %s' % name, os.path.join(os.path.expanduser('~/Downloads'), '%s.apk' % app['package']), 'Android apps (*.apk)')
  if not path:
   return
  if not self.window_.begin_operation():
   return
  self.abort = threading.Event()
  abort, backend = self.abort, self.window_.backend
  self.cancel.show()
  self.show_progress(None, 'Downloading %s' % name)

  def work(emit):
   return backend.download(app, path, lambda d, t: emit(100 * d / t if t else None, 'Downloading %s' % name), abort)

  def done(result):
   self.finish('%s saved. Nothing was installed.' % name)
   self.window_.end_operation()

  def failed(error):
   self.window_.end_operation()
   self.finish('Download cancelled.' if isinstance(error, DownloadCancelledError) else 'Download failed: %s' % error)

  run_job(work, done, failed, lambda p, m: self.show_progress(p, m))

 def sync(self):
  if not self.window_.begin_operation():
   return
  self.cancel.hide()
  self.show_progress(None, 'Checking for updates')
  backend = self.window_.backend

  def done(value):
   apps, result = value
   self.set_apps(apps)
   self.window_.end_operation()
   self.finish('Catalog is current.' if result.success else 'Some updates failed: %s' % '; '.join(result.errors[:2]))

  def failed(error):
   self.window_.end_operation()
   self.finish('Update check failed: %s' % error)

  run_job(lambda emit: backend.sync_catalog(force=True), done, failed)
