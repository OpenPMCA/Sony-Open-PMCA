"""Qt plumbing: stdout capture, background jobs, camera polling."""
import sys
import threading

from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, Signal


class LogBus(QObject):
 """Replaces stdout/stderr so everything the backend prints becomes Activity lines."""
 line = Signal(str)

 def __init__(self, parent=None):
  QObject.__init__(self, parent)
  self._buffer = ''
  self._lock = threading.Lock()
  self._originals = (sys.stdout, sys.stderr)

 def install(self):
  sys.stdout = sys.stderr = self

 def uninstall(self):
  sys.stdout, sys.stderr = self._originals

 def write(self, text):
  if not text:
   return 0
  with self._lock:
   self._buffer += text
   *lines, self._buffer = self._buffer.split('\n')
  for line in lines:
   self.line.emit(line.rstrip('\r'))
  return len(text)

 def flush(self):
  pass

 def isatty(self):
  return False


class _JobSignals(QObject):
 progress = Signal(object, str)
 done = Signal(object)
 failed = Signal(object)


class Job(QRunnable):
 """Runs fn(emit) on the thread pool. emit(percent_or_None, message) reports progress."""

 def __init__(self, fn):
  QRunnable.__init__(self)
  self.fn = fn
  self.signals = _JobSignals()
  self.setAutoDelete(False)

 def run(self):
  try:
   result = self.fn(self.signals.progress.emit)
  except BaseException as error:
   self.signals.failed.emit(error)
  else:
   self.signals.done.emit(result)


_live = set()


def run_job(fn, on_done=None, on_failed=None, on_progress=None):
 """Start fn on the shared pool; callbacks run on the GUI thread."""
 job = Job(fn)
 _live.add(job)

 def finish(callback):
  def wrapper(value):
   _live.discard(job)
   if callback:
    callback(value)
  return wrapper

 job.signals.done.connect(finish(on_done))
 job.signals.failed.connect(finish(on_failed))
 if on_progress:
  job.signals.progress.connect(on_progress)
 QThreadPool.globalInstance().start(job)
 return job


class CameraMonitor(QThread):
 """Polls camera status; paused while an operation owns the camera."""
 status = Signal(object)

 def __init__(self, poll, interval=3.0, parent=None):
  QThread.__init__(self, parent)
  self._poll = poll
  self._interval = interval
  self._stop = threading.Event()
  self._paused = threading.Event()

 def pause(self, paused):
  if paused:
   self._paused.set()
  else:
   self._paused.clear()

 def stop(self):
  self._stop.set()
  self.wait(5000)

 def run(self):
  while not self._stop.is_set():
   if not self._paused.is_set():
    try:
     self.status.emit(self._poll())
    except Exception as error:
     print('Camera monitor error: %s' % error)
   if self._stop.wait(self._interval):
    break
