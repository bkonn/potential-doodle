# Personal Assistant Foundation

A small, runnable starting point for a personal assistant: persistent local memory with sources and confidence labels, plus a task ledger that requires evidence before marking work complete.

This is a command-line foundation, not yet a conversational AI or an always-running assistant. It does not browse, import chat history, access accounts, send messages, or run background jobs.

## Setup

Python 3.10 or newer, with SQLite support. No third-party dependencies or API keys required.

```sh
python3 assistant.py init
python3 assistant.py brief
python3 -m unittest discover -v
```

The setup command is `python3 assistant.py init`. The entry point is `python3 assistant.py`; use `--help` for commands. There is no web server or port to configure.

## Use

```sh
python3 assistant.py remember "I prefer concise responses" --source "Direct user statement" --status confirmed
python3 assistant.py task "Review my upcoming deadlines"
python3 assistant.py brief
python3 assistant.py done 1 --evidence "Reviewed calendar and confirmed with user"
python3 assistant.py forget 1
```

Memories default to `uncertain`; supported labels are `confirmed`, `uncertain`, and `outdated`. To correct a memory, remove it by ID and add the corrected statement with its source. Completion evidence is a recorded assertion, not an independent verification of external work.

## Personal data

The default database is `~/.local/share/personal-assistant/assistant.db`, outside this repository. Override with `ASSISTANT_DB` or `--db PATH` before the subcommand. The database is not encrypted; protect it using your device access controls and encrypted storage. Keep private backups. Deletion removes a record from the application, not necessarily from backups or recoverable disk pages.

This public repository contains only code and generic examples. Do not commit personal history, account exports, private profiles, credentials, or database files. `brief` prints stored data to your terminal, so avoid sharing its output inadvertently.

## Next implementation steps

1. Import user-provided conversation exports into private storage with source references and duplicate detection.
2. Add user review for conflicting or outdated facts and identity checks for public-web findings.
3. Connect a chosen language model to retrieve relevant memories.
4. Add selected account integrations and an explicit action-permission policy.
5. Add scheduling and an auditable execution log, then a voice or chat interface.

No integrations or scheduled actions are enabled by this starter.

## History import

Import private source files outside the repository. Use the same database as the assistant:

```sh
python3 history.py --db ~/.local/share/personal-assistant/assistant.db chatgpt /private/path/conversations.json
python3 history.py --db ~/.local/share/personal-assistant/assistant.db text /private/path/history.md --source "History supplement, dated YYYY-MM-DD"
python3 history.py --db ~/.local/share/personal-assistant/assistant.db search "preferences"
```

The ChatGPT importer accepts a JSON array of conversations with IDs and message mappings. It retains text messages from all branches, their roles, source IDs and timestamps. It does not import images, audio or attachments. Exact duplicate records are skipped. Invalid batches roll back. Imported text is reference material, not executable instructions, verified personal facts, or completed tasks. The `brief` command shows curated memories/tasks; `history.py search` retrieves the separate source archive.

For other exports, `history.py --db PATH records FILE.json` accepts an array of objects containing `source`, `role`, `body`, and optional `source_time`. This is a local import interface, not an account connection or automatic sync. ChatGPT-hosted account connections and credentials are not transferred to this program.
