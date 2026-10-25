"""Import source history as reference data, never as instructions or verified facts."""
import argparse
import hashlib
import json
from pathlib import Path

from assistant import connect


def import_records(db, records):
    db.execute('''CREATE TABLE IF NOT EXISTS history (
        digest TEXT PRIMARY KEY, source TEXT NOT NULL, role TEXT NOT NULL,
        body TEXT NOT NULL, source_time TEXT, imported_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    count = 0
    with db:
        for record in records:
            source, role, body = (record[key] for key in ('source', 'role', 'body'))
            if not all(isinstance(value, str) and value.strip() for value in (source, role, body)):
                raise ValueError('Each record requires nonempty source, role and body strings')
            stamp = record.get('source_time')
            canonical = json.dumps([source, role, body, stamp], ensure_ascii=False)
            digest = hashlib.sha256(canonical.encode()).hexdigest()
            count += db.execute(
                'INSERT OR IGNORE INTO history (digest, source, role, body, source_time) VALUES (?,?,?,?,?)',
                (digest, source, role, body, None if stamp is None else str(stamp))).rowcount
    return count


def chatgpt_records(conversations):
    if not isinstance(conversations, list):
        raise ValueError('Expected a conversations JSON array')
    for conversation in conversations:
        identity = conversation.get('id') or conversation.get('conversation_id')
        if not identity or not isinstance(conversation.get('mapping'), dict):
            raise ValueError('Conversation requires an ID and mapping')
        for node_id, node in conversation['mapping'].items():
            message = node.get('message')
            if not message:
                continue
            parts = (message.get('content') or {}).get('parts', [])
            body = '\n'.join(part for part in parts if isinstance(part, str))
            if not body.strip():
                continue
            yield {'source': f'chatgpt:{identity}:{node_id}',
                   'role': (message.get('author') or {}).get('role') or 'unknown',
                   'body': body, 'source_time': message.get('create_time')}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('chatgpt', 'records'):
        command = commands.add_parser(name)
        command.add_argument('file', type=Path)
    text = commands.add_parser('text')
    text.add_argument('file', type=Path)
    text.add_argument('--source', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    db = None
    args = parser.parse_args(argv)
    try:
        if args.command == 'search':
            db = connect(args.db)
            import_records(db, [])
            rows = db.execute('SELECT source, role, body, source_time FROM history WHERE instr(lower(body), lower(?)) > 0 LIMIT 20', (args.query,))
            print(json.dumps([dict(row) for row in rows], indent=2))
        else:
            raw = args.file.read_text(encoding='utf-8')
            if args.command == 'text':
                records = [{'source': args.source, 'role': 'reference', 'body': raw}]
            elif args.command == 'chatgpt':
                records = chatgpt_records(json.loads(raw))
            else:
                records = json.loads(raw)
                if not isinstance(records, list):
                    raise ValueError('Expected a records JSON array')
            db = connect(args.db)
            print(json.dumps({'inserted': import_records(db, records)}))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.error(f'Import/search failed: {error}')
    finally:
        if db is not None:
            db.close()


if __name__ == '__main__':
    main()
