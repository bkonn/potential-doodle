"""Local memory and task foundation. No network calls or model credentials."""
import argparse
import json
import os
import sqlite3
from pathlib import Path


def connect(path):
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY, fact TEXT NOT NULL, source TEXT NOT NULL,
            status TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', evidence TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    return db


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=os.environ.get(
        'ASSISTANT_DB', '~/.local/share/personal-assistant/assistant.db'))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('init')
    remember = commands.add_parser('remember')
    remember.add_argument('fact')
    remember.add_argument('--source', required=True)
    remember.add_argument('--status', choices=['confirmed', 'uncertain', 'outdated'],
                          default='uncertain')
    task = commands.add_parser('task')
    task.add_argument('title')
    done = commands.add_parser('done')
    done.add_argument('id', type=int)
    done.add_argument('--evidence', required=True)
    forget = commands.add_parser('forget')
    forget.add_argument('id', type=int)
    commands.add_parser('brief')
    args = parser.parse_args(argv)
    for field in ('fact', 'source', 'title', 'evidence'):
        if hasattr(args, field) and not getattr(args, field).strip():
            parser.error(f'{field} must not be blank')
    db = connect(args.db)
    try:
        with db:
            if args.command == 'remember':
                db.execute('INSERT INTO memories (fact, source, status) VALUES (?, ?, ?)',
                           (args.fact, args.source, args.status))
            elif args.command == 'task':
                db.execute('INSERT INTO tasks (title) VALUES (?)', (args.title,))
            elif args.command == 'done':
                result = db.execute("UPDATE tasks SET status='completed', evidence=? WHERE id=?",
                                    (args.evidence, args.id))
                if not result.rowcount:
                    parser.error('Task not found')
            elif args.command == 'forget':
                result = db.execute('DELETE FROM memories WHERE id=?', (args.id,))
                if not result.rowcount:
                    parser.error('Memory not found')
        if args.command == 'brief':
            print(json.dumps({
                'memories': [dict(row) for row in db.execute('SELECT * FROM memories ORDER BY id')],
                'tasks': [dict(row) for row in db.execute('SELECT * FROM tasks ORDER BY id')],
            }, indent=2))
        else:
            print('Saved locally.')
    finally:
        db.close()


if __name__ == '__main__':
    main()
