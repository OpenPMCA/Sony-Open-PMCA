"""Pure view state derived from backend status dicts. No Qt, no USB."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraState:
 kind: str  # 'none' | 'unusable' | 'ready' | 'installer'
 name: str = ''
 mode: str = ''
 reason: str = ''
 can_install: bool = False
 install_reason: str = ''
 serial: str = ''

 @property
 def identity(self):
  return (self.name, self.serial)

 @property
 def connected(self):
  return self.kind in ('ready', 'installer')


NO_CAMERA = CameraState('none')

STEPS = (
 'On the camera open Menu, Setup, USB Connection and choose MTP.',
 'Connect a USB data cable and switch the camera on.',
 'Close Photos and Image Capture if they open.',
)


def from_status(info):
 """Map getCameraStatus() output to a CameraState."""
 if not info:
  return NO_CAMERA
 name = info.get('name') or info.get('model') or 'Sony camera'
 mode = info.get('mode') or ''
 if info.get('appConnected'):
  can = bool(info.get('app_installation_supported'))
  reason = info.get('app_installation_reason') or ''
  if info.get('busy'):
   can, reason = False, 'The camera is busy with another operation.'
  serial = str(info.get('serial') or info.get('raw_serial') or '')
  kind = 'installer' if mode == 'App installation' else 'ready'
  return CameraState(kind, name, mode, '', can, reason, serial)
 physical = info.get('physicalDetected') or info.get('connected') or info.get('status') in (
  'access_denied', 'unverified', 'multiple_devices', 'msc_excluded', 'wrong_mode', 'unsupported_mode')
 if not physical:
  return NO_CAMERA
 status = str(info.get('status') or '')
 if status == 'multiple_devices':
  reason = info.get('failure_reason') or 'More than one Sony camera is connected. Leave only one.'
 elif 'Mass Storage' in mode or 'MSC' in mode or status in ('msc_excluded', 'wrong_mode', 'unsupported_mode'):
  reason = info.get('failure_reason') or 'The camera is in Mass Storage mode. Set USB Connection to MTP.'
 elif 'access_denied' in status:
  reason = info.get('failure_reason') or 'USB access was denied.'
 else:
  reason = info.get('failure_reason') or 'The camera is connected but not answering over MTP.'
 return CameraState('unusable', name, mode, reason)


def support_text(model, info=None):
 """One-line app support statement for a model."""
 from pmca.compatibility import get_camera_support
 support = get_camera_support(model) if model else {}
 apps = support.get('pmca_apps')
 if apps is True:
  return 'Supported, verified on this model' if support.get('installation_tested') else 'Supported by the PMCA reference list'
 if apps is False:
  return 'Not supported, no PMCA subsystem'
 return 'Unconfirmed model'


def describe(props, state):
 """Group read-only camera properties into display sections: [(title, [(label, value, note)])]."""
 p = props or {}

 def row(label, key, note_key=None):
  value = p.get(key)
  if value in (None, '') or str(value).startswith('Unavailable'):
   return None
  note = p.get(note_key) if note_key else None
  return (label, str(value), str(note) if note else '')

 identity = [row('Model', 'Model'), row('Product code', 'Product code'), row('Serial number', 'Serial number'),
             row('Firmware', 'Firmware version'), row('Lens', 'Lens')]
 usage = [row('Shutter count', 'Shutter count', 'Shutter note'), row('GPS data', 'GPS Data')]
 link = [row('USB mode', 'USB mode'), row('PTP version', 'PTP version')]
 sections = [('Camera', identity), ('Usage', usage), ('Connection', link)]
 out = []
 for title, rows in sections:
  rows = [r for r in rows if r]
  if title == 'Camera':
   rows.insert(1 if rows else 0, ('Apps', support_text(p.get('Model') or state.name), ''))
  if rows:
   out.append((title, rows))
 return out
