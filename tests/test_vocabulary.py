"""GoldenDict defaults and Anki setup: temporary files and mocked API only."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'lib/vocabulary/scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gd = load('configure_goldendict', 'configure-goldendict.py')
lm = load('apply_longman', 'apply-longman.py')


class GoldenDict(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / 'goldendict/config'

    def test_fresh_install_has_no_dictionary_or_demo_sources(self):
        self.assertTrue(gd.configure(self.config))
        root = ET.parse(self.config).getroot()
        self.assertEqual(root.findall('./paths/path'), [])
        for tag in ('mediawikis', 'websites', 'dictservers', 'programs', 'voiceEngines'):
            self.assertIsNotNone(root.find(tag))
            self.assertEqual(len(root.find(tag)), 0)
        self.assertEqual(root.findtext('./preferences/darkReaderMode'), '0')
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)
        before = self.config.stat().st_mtime_ns
        self.assertFalse(gd.configure(self.config))
        self.assertEqual(self.config.stat().st_mtime_ns, before)

    def test_disables_sources_preserves_local_paths_groups_and_unmanaged_preferences(self):
        self.config.parent.mkdir()
        self.config.write_text('''<config><!--keep--><paths><path recursive="1">/books</path></paths>
          <groups><group id="7" name="Mine"/></groups><preferences><zoomFactor>1.5</zoomFactor></preferences>
          <dictservers><server name="dict.org" enabled="1" url="dict://dict.org"/></dictservers>
          <websites><website name="Custom" enabled="1" url="https://example.org"/></websites>
          <forvo><enable>1</enable><apiKey>keep</apiKey></forvo></config>''')
        self.config.chmod(0o640)
        gd.configure(self.config)
        root = ET.parse(self.config).getroot()
        self.assertEqual(root.find('./paths/path').attrib, {'recursive': '1'})
        self.assertEqual(root.findtext('./paths/path'), '/books')
        self.assertEqual(root.find('./groups/group').get('name'), 'Mine')
        self.assertEqual(root.findtext('./preferences/zoomFactor'), '1.5')
        self.assertEqual(root.find('./dictservers/server').get('enabled'), '0')
        self.assertEqual(root.find('./websites/website').get('enabled'), '0')
        self.assertEqual(root.findtext('./forvo/enable'), '0')
        self.assertEqual(root.findtext('./forvo/apiKey'), 'keep')
        self.assertIn('<!--keep-->', self.config.read_text())
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o640)

    def test_check_does_not_create_or_modify_file(self):
        self.assertTrue(gd.configure(self.config, check=True))
        self.assertFalse(self.config.parent.exists())
        gd.configure(self.config)
        before = self.config.read_bytes()
        self.assertTrue(gd.configure(self.config, Path('/new-dictionary'), check=True))
        self.assertEqual(self.config.read_bytes(), before)

    def test_dictionary_path_is_opt_in_and_not_duplicated(self):
        gd.configure(self.config, Path('/dictionary'))
        self.assertFalse(gd.configure(self.config, Path('/dictionary')))
        self.assertEqual(len(ET.parse(self.config).findall('./paths/path')), 1)

    def test_symlink_is_rejected_without_modifying_target(self):
        self.config.parent.mkdir()
        target = self.config.parent / 'target'
        target.write_text('<config/>')
        self.config.symlink_to(target)
        with self.assertRaises(RuntimeError):
            gd.configure(self.config)
        self.assertEqual(target.read_text(), '<config/>')

    def test_check_works_while_app_runs(self):
        gd.configure(self.config)
        with patch.object(sys, 'argv', ['configure', '--config', str(self.config), '--check']), patch.object(gd, 'goldendict_running') as running:
            gd.main()
        running.assert_not_called()


class AnkiSetup(unittest.TestCase):
    def setUp(self):
        self.assets = ROOT / 'lib/vocabulary/assets/anki'
        self.templates = {'Card 1': {
            'Front': (self.assets / 'longman-front.html').read_text(),
            'Back': (self.assets / 'longman-back.html').read_text(),
        }}
        self.css = (self.assets / 'longman.css').read_text()
        self.calls = []

    def api(self, action, **params):
        self.calls.append(action)
        return {
            'version': 6, 'modelNames': ['Longman'], 'deckNames': ['LongMan'],
            'modelFieldNames': ['Word', 'selected_text', 'marked_sentence'],
            'modelTemplates': self.templates, 'modelStyling': {'css': self.css},
        }[action]

    def run_main(self, *args, api=None):
        with patch.object(sys, 'argv', ['apply-longman', *args]), patch.object(lm, 'anki', side_effect=api or self.api):
            lm.main()

    def test_check_and_repeat_setup_do_not_mutate_collection(self):
        self.run_main('--check')
        self.run_main()
        self.assertTrue(set(self.calls) <= {'version', 'modelNames', 'deckNames', 'modelFieldNames', 'modelTemplates', 'modelStyling'})

    def test_check_mismatch_does_not_apply_templates(self):
        def api(action, **params):
            return {'css': 'old'} if action == 'modelStyling' else self.api(action, **params)
        with self.assertRaisesRegex(RuntimeError, 'templates or CSS differ'):
            self.run_main('--check', api=api)
        self.assertNotIn('updateModelTemplates', self.calls)

    def test_missing_model_does_not_create_empty_collection(self):
        def api(action, **params):
            return [] if action == 'modelNames' else self.api(action, **params)
        with self.assertRaisesRegex(RuntimeError, 'Sync your existing'):
            self.run_main(api=api)
        self.assertNotIn('createModel', self.calls)
        self.assertNotIn('createDeck', self.calls)

    def test_check_cannot_initialize(self):
        with self.assertRaises(SystemExit) as error:
            self.run_main('--check', '--initialize')
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.calls, [])

    def test_busy_and_connection_errors_are_actionable(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'result': None, 'error': 'Collection lifecycle operation is active.'}).encode()
        with patch.object(lm, 'urlopen', return_value=response), self.assertRaisesRegex(RuntimeError, 'Finish import/sync'):
            lm.anki('modelNames')
        with patch.object(lm, 'urlopen', side_effect=URLError('connection refused')), self.assertRaisesRegex(RuntimeError, 'Open Anki'):
            lm.anki('version')


if __name__ == '__main__':
    unittest.main()
