import unittest
from assistant import connect
from history import chatgpt_records, import_records


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.db = connect(':memory:')
        self.addCleanup(self.db.close)

    def test_reimport_deduplicates_and_preserves_role(self):
        records = list(chatgpt_records([{'id': 'c1', 'mapping': {'n1': {'message': {
            'author': {'role': 'assistant'}, 'content': {'parts': ['An unverified claim']},
            'create_time': 123}}}}]))
        self.assertEqual(import_records(self.db, records), 1)
        self.assertEqual(import_records(self.db, records), 0)
        self.assertEqual(self.db.execute('SELECT role FROM history').fetchone()[0], 'assistant')
        self.assertEqual(self.db.execute('SELECT count(*) FROM memories').fetchone()[0], 0)

    def test_failed_batch_rolls_back(self):
        with self.assertRaises(ValueError):
            import_records(self.db, [{'source': 'a', 'role': 'user', 'body': 'test'},
                                     {'source': '', 'role': 'user', 'body': 'bad'}])
        self.assertEqual(self.db.execute('SELECT count(*) FROM history').fetchone()[0], 0)

    def test_branch_messages_kept_and_nontext_skipped(self):
        records = list(chatgpt_records([{'id': 'c1', 'mapping': {
            'root': {'message': None},
            'a': {'message': {'author': {'role': 'user'}, 'content': {'parts': ['Hello', {'image': 'ref'}]}}},
            'b': {'message': {'author': {'role': 'assistant'}, 'content': {'parts': ['Hi']}}}
        }}]))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['body'], 'Hello')


if __name__ == '__main__':
    unittest.main()
