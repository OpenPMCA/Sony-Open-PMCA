"""Sony Open PMCA application entry point."""
import json
import os
import platform
import sys

SCRIPT_ROOT = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)) + '/..')

if getattr(sys, 'frozen', False):
 from frozenversion import version
else:
 from pmca import __version__ as version


def check_runtime(out_file):
 """Verify packaged dependencies without opening a window or a USB device."""
 import tlslite
 from PySide6.QtCore import qVersion
 from pmca import spk
 from pmca.commands.usb import getFdats

 libusb_loads, libusb_path = False, None
 try:
  import usb.backend.libusb1
  find_lib = None
  if sys.platform == 'win32':
   try:
    import libusb_package
    find_lib = libusb_package.find_library
   except ImportError:
    pass
  library = usb.backend.libusb1._load_library(find_library=find_lib) if find_lib else usb.backend.libusb1._load_library()
  if library:
   libusb_loads = bool(getattr(library, 'libusb_get_version', None))
   libusb_path = str(getattr(library, '_name', 'libusb'))
 except Exception:
  pass

 cert = os.path.join(SCRIPT_ROOT, 'certs/localtest.me.pem')
 with open(cert) as f:
  pem = f.read()
 chain = tlslite.X509CertChain()
 chain.parsePemList(pem)
 key = tlslite.parsePEMKey(pem, private=True)
 sample = b'Sony Open PMCA runtime check'
 result = {
  'version': version or '',
  'python': platform.python_version(),
  'architecture': platform.machine(),
  'frozen': bool(getattr(sys, 'frozen', False)),
  'qt_version': qVersion(),
  'libusb_loads': libusb_loads,
  'libusb_path': libusb_path,
  'spk_roundtrip': spk.parse(spk.dump(sample)) == sample,
  'certificate_key_parses': bool(chain.x509List and key),
  'updater_images': len(list(getFdats())),
 }
 try:
  from pmca.marketserver.server import verify_tls_handshake
  info = verify_tls_handshake(certFile=cert)
  if isinstance(info, dict):
   result['tls_handshake_verified'] = info.get('success') is True
   for field in ('cipher', 'version'):
    if info.get(field):
     result['tls_' + field] = info[field]
   if info.get('success') is not True and info.get('error'):
    result['tls_error'] = str(info['error'])
  else:
   result['tls_handshake_verified'] = info is True
 except Exception as error:
  result['tls_handshake_verified'] = False
  result['tls_error'] = str(error)
 with open(out_file, 'w') as f:
  json.dump(result, f, indent=2)


def main(argv=None):
 argv = list(sys.argv if argv is None else argv)
 if len(argv) == 3 and argv[1] == '--check-runtime':
  check_runtime(argv[2])
  return 0
 from PySide6.QtWidgets import QApplication
 from .backend import Backend
 from .ui.runtime import LogBus
 from .ui.window import MainWindow

 app = QApplication(argv)
 app.setApplicationName('Sony Open PMCA')
 app.setOrganizationName('OpenPMCA')
 bus = LogBus()
 bus.install()
 window = MainWindow(Backend(), version, os.path.join(SCRIPT_ROOT, 'assets/sony-open-pmca.png'))
 bus.line.connect(window.activity_page.add)
 window.show()
 window.start()
 try:
  return app.exec()
 finally:
  bus.uninstall()
