import uuid
import datetime

class LedgerEntry:
    """Represents a single entry in a document's ledger."""
    def __init__(self, title: str, entry_type: str, jurisdiction_tag: str,
                 notes: str = "", associated_clause_ids: list[str] = None,
                 status: str = "Active", entry_id: str = None, timestamp: str = None):
        self.entry_id = entry_id if entry_id else f"LENT-{uuid.uuid4().hex[:8].upper()}"
        self.timestamp = timestamp if timestamp else datetime.datetime.now().isoformat()
        self.title = title
        self.entry_type = entry_type # E.g., "Transaction", "Notice", "Filing", "Clause Reference"
        self.jurisdiction_tag = jurisdiction_tag # E.g., "Lex Aequies", "Lex Postalis"
        self.notes = notes
        self.associated_clause_ids = associated_clause_ids if associated_clause_ids is not None else []
        self.status = status # E.g., "Active", "Archived", "Under Review"

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "title": self.title,
            "entry_type": self.entry_type,
            "jurisdiction_tag": self.jurisdiction_tag,
            "notes": self.notes,
            "associated_clause_ids": self.associated_clause_ids,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            title=data.get("title", "Untitled Entry"),
            entry_type=data.get("entry_type", "Generic"),
            jurisdiction_tag=data.get("jurisdiction_tag", "Unknown"),
            notes=data.get("notes", ""),
            associated_clause_ids=data.get("associated_clause_ids", []),
            status=data.get("status", "Active"),
            entry_id=data.get("entry_id"), # Let constructor generate if None
            timestamp=data.get("timestamp") # Let constructor generate if None
        )

    def __str__(self):
        return f"{self.timestamp[:19]} - {self.entry_type}: {self.title[:50]}"


class DocumentLedger:
    """Holds and manages ledger entries for a specific document."""
    def __init__(self, document_id: str, ledger_id: str = None):
        self.ledger_id = ledger_id if ledger_id else f"LEDG-{uuid.uuid4().hex[:8].upper()}"
        self.document_id = document_id # ID of the document this ledger belongs to
        self.entries: list[LedgerEntry] = []

    def add_entry(self, entry: LedgerEntry = None, **entry_data_kwargs):
        """Adds a new entry to the ledger. Can accept a LedgerEntry object or kwargs to create one."""
        if entry and isinstance(entry, LedgerEntry):
            self.entries.append(entry)
        elif entry_data_kwargs:
            new_entry = LedgerEntry(**entry_data_kwargs)
            self.entries.append(new_entry)
        else:
            raise ValueError("add_entry requires either a LedgerEntry object or keyword arguments for a new entry.")
        # Sort entries by timestamp, most recent first (optional, can be done at display time)
        self.entries.sort(key=lambda x: x.timestamp, reverse=True)


    def to_dict(self) -> dict:
        return {
            "ledger_id": self.ledger_id,
            "document_id": self.document_id,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict, document_id_override: str = None):
        # document_id_override is useful if the ledger is part of a document being loaded,
        # ensuring the ledger's document_id matches the parent document.
        doc_id = document_id_override if document_id_override else data.get("document_id", "UNKNOWN_DOC_ID")

        ledger = cls(document_id=doc_id, ledger_id=data.get("ledger_id"))

        entries_data = data.get("entries", [])
        for entry_data in entries_data:
            ledger.entries.append(LedgerEntry.from_dict(entry_data))

        # Maintain sort order if needed, e.g., by timestamp
        ledger.entries.sort(key=lambda x: x.timestamp, reverse=True)
        return ledger


if __name__ == '__main__':
    # Test LedgerEntry
    entry1 = LedgerEntry(title="Initial Trust Setup", entry_type="System Event", jurisdiction_tag="Lex Aequies", notes="Trust object created.")
    print(f"Entry 1: {entry1}")
    print(f"Entry 1 dict: {entry1.to_dict()}")
    entry1_reloaded = LedgerEntry.from_dict(entry1.to_dict())
    assert entry1_reloaded.title == entry1.title

    # Test DocumentLedger
    doc_id_test = f"DOC-{uuid.uuid4().hex[:4]}"
    ledger = DocumentLedger(document_id=doc_id_test)
    ledger.add_entry(title="First Clause Added", entry_type="Clause Management", jurisdiction_tag="Lex Aequies", notes="Added primary dominion clause.")
    ledger.add_entry(entry=entry1) # Adding pre-created entry

    print(f"\nLedger for Doc ID: {ledger.document_id} (Ledger ID: {ledger.ledger_id})")
    for e in ledger.entries:
        print(f"  - {e}")

    ledger_dict = ledger.to_dict()
    print(f"\nLedger dict: {json.dumps(ledger_dict, indent=2)}")

    ledger_reloaded = DocumentLedger.from_dict(ledger_dict, document_id_override=doc_id_test)
    assert ledger_reloaded.ledger_id == ledger.ledger_id
    assert len(ledger_reloaded.entries) == len(ledger.entries)
    assert ledger_reloaded.entries[0].title == ledger.entries[0].title # Assuming sort order is maintained

    print("\nAll Ledger Models tests passed (conceptual).")
