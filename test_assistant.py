import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from assistant import main


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = str(Path(self.directory.name) / 'memory.db')

    def run_cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(['--db', self.db, *args])
        return output.getvalue()

    def test_memory_persists_with_source_and_can_be_removed(self):
        self.run_cli('remember', 'Example preference', '--source', 'User statement')
        memory = json.loads(self.run_cli('brief'))['memories'][0]
        self.assertEqual(memory['source'], 'User statement')
        self.assertEqual(memory['status'], 'uncertain')
        self.run_cli('forget', str(memory['id']))
        self.assertEqual(json.loads(self.run_cli('brief'))['memories'], [])

    def test_task_stays_pending_until_completion_has_evidence(self):
        self.run_cli('task', 'Example task')
        self.assertEqual(json.loads(self.run_cli('brief'))['tasks'][0]['status'], 'pending')
        self.run_cli('done', '1', '--evidence', 'User confirmed completion')
        task = json.loads(self.run_cli('brief'))['tasks'][0]
        self.assertEqual(task['status'], 'completed')
        self.assertEqual(task['evidence'], 'User confirmed completion')

    def test_blank_evidence_rejected(self):
        self.run_cli('task', 'Example task')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.run_cli('done', '1', '--evidence', ' ')
        self.assertEqual(json.loads(self.run_cli('brief'))['tasks'][0]['status'], 'pending')


if __name__ == '__main__':
    unittest.main()
