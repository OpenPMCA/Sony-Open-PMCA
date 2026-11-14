import unittest

from pmca_app import state as st


class StateTest(unittest.TestCase):
 def test_no_status_means_no_camera(self):
  self.assertEqual(st.from_status(None), st.NO_CAMERA)
  self.assertEqual(st.from_status({'physicalDetected': False}).kind, 'none')

 def test_ready_camera_carries_install_support(self):
  s = st.from_status({'appConnected': True, 'name': 'ILCE-7', 'mode': 'MTP', 'serial': '123',
                      'app_installation_supported': True})
  self.assertEqual((s.kind, s.name, s.can_install, s.identity), ('ready', 'ILCE-7', True, ('ILCE-7', '123')))

 def test_busy_camera_cannot_install(self):
  s = st.from_status({'appConnected': True, 'name': 'ILCE-7', 'app_installation_supported': True, 'busy': True})
  self.assertFalse(s.can_install)
  self.assertIn('busy', s.install_reason)

 def test_installer_mode_is_connected_but_distinct(self):
  s = st.from_status({'appConnected': True, 'name': 'ILCE-7', 'mode': 'App installation'})
  self.assertEqual(s.kind, 'installer')
  self.assertTrue(s.connected)

 def test_usb_without_mtp_explains_why(self):
  s = st.from_status({'physicalDetected': True, 'name': 'ILCE-7', 'mode': 'Mass Storage (Class 8)'})
  self.assertEqual(s.kind, 'unusable')
  self.assertIn('MTP', s.reason)
  s = st.from_status({'physicalDetected': True, 'status': 'multiple_devices', 'name': 'x'})
  self.assertIn('one', s.reason)

 def test_describe_groups_and_hides_unavailable_values(self):
  state = st.from_status({'appConnected': True, 'name': 'ILCE-7'})
  props = {'Model': 'ILCE-7', 'Serial number': '1', 'Firmware version': 'Unavailable (read-only MTP)',
           'Shutter count': '49,510 actuations', 'Shutter note': 'sample image', 'USB mode': 'MTP'}
  sections = dict(st.describe(props, state))
  labels = [r[0] for r in sections['Camera']]
  self.assertNotIn('Firmware', labels)
  self.assertIn('Apps', labels)
  self.assertEqual(sections['Usage'][0], ('Shutter count', '49,510 actuations', 'sample image'))

 def test_support_text_matches_reference_list(self):
  self.assertIn('verified', st.support_text('ILCE-7'))
  self.assertIn('Not supported', st.support_text('NEX-5'))
  self.assertEqual(st.support_text('ILCE-9999'), 'Unconfirmed model')


if __name__ == '__main__':
 unittest.main()
