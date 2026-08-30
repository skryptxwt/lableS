"""Bounded per-image annotation history used by undo and redo."""

from collections import OrderedDict
from dataclasses import dataclass


def _freeze(rows):
    return tuple(tuple(value for value in row) for row in rows)


def _thaw(state):
    return [list(row) for row in state]


@dataclass(frozen=True)
class HistoryEntry:
    state: tuple
    action: str


class AnnotationHistory:
    """Keep independent, bounded histories for recently edited images."""

    def __init__(self, limit=80, document_limit=24):
        self.limit = max(2, int(limit))
        self.document_limit = max(1, int(document_limit))
        self._documents = OrderedDict()

    def activate(self, key, rows):
        """Synchronize a document, preserving history when state still matches."""
        state = _freeze(rows)
        document = self._documents.get(key)
        if (document is None
                or document['entries'][document['cursor']].state != state):
            document = {
                'entries': [HistoryEntry(state, '初始状态')],
                'cursor': 0,
            }
            self._documents[key] = document
        self._touch(key)

    def record(self, key, rows, action):
        """Append a committed state; equal consecutive states are ignored."""
        state = _freeze(rows)
        document = self._documents.get(key)
        if document is None:
            self.activate(key, rows)
            return False
        entries = document['entries']
        cursor = document['cursor']
        if entries[cursor].state == state:
            self._touch(key)
            return False
        del entries[cursor + 1:]
        entries.append(HistoryEntry(state, str(action)))
        if len(entries) > self.limit:
            del entries[:len(entries) - self.limit]
        document['cursor'] = len(entries) - 1
        self._touch(key)
        return True

    def undo(self, key):
        document = self._documents.get(key)
        if document is None or document['cursor'] <= 0:
            return None
        action = document['entries'][document['cursor']].action
        document['cursor'] -= 1
        self._touch(key)
        return _thaw(document['entries'][document['cursor']].state), action

    def redo(self, key):
        document = self._documents.get(key)
        if (document is None
                or document['cursor'] >= len(document['entries']) - 1):
            return None
        document['cursor'] += 1
        entry = document['entries'][document['cursor']]
        self._touch(key)
        return _thaw(entry.state), entry.action

    def can_undo(self, key):
        document = self._documents.get(key)
        return bool(document is not None and document['cursor'] > 0)

    def can_redo(self, key):
        document = self._documents.get(key)
        return bool(document is not None
                    and document['cursor'] < len(document['entries']) - 1)

    def has_document(self, key):
        return key in self._documents

    def _touch(self, key):
        self._documents.move_to_end(key)
        while len(self._documents) > self.document_limit:
            self._documents.popitem(last=False)
