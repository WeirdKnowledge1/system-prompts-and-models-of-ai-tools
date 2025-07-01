import uuid
import datetime

class Clause:
    """
    Represents a single clause within a document.
    Part IV.A - Rudimentary Clause Engine
    """
    def __init__(self, text: str, clause_id: str = None,
                 jurisdiction: str = "Lex Aequies", origin: str = "User Input"):
        self.id = clause_id if clause_id else f"CL-{uuid.uuid4().hex[:8].upper()}"
        self.text = text
        self.jurisdiction = jurisdiction # E.g., "Lex Aequies", "Lex Postalis", "Lex Naturalis"
        self.origin = origin # E.g., "User Input", "Template", "Uploaded Doc", "AI Generated"
        self.creation_date = datetime.datetime.now().isoformat()
        self.last_modified_date = self.creation_date
        self.version = 1
        self.metadata = {} # For future use, e.g., linkage, validation status

    def update_text(self, new_text: str):
        self.text = new_text
        self.last_modified_date = datetime.datetime.now().isoformat()
        self.version += 1

    def update_jurisdiction(self, new_jurisdiction: str):
        self.jurisdiction = new_jurisdiction
        self.last_modified_date = datetime.datetime.now().isoformat()
        self.version += 1

    def __str__(self):
        return f"ID: {self.id} ({self.jurisdiction}) - {self.text[:50]}{'...' if len(self.text) > 50 else ''}"

    def to_dict(self) -> dict:
        """Serializes the clause to a dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "jurisdiction": self.jurisdiction,
            "origin": self.origin,
            "creation_date": self.creation_date,
            "last_modified_date": self.last_modified_date,
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserializes a clause from a dictionary."""
        clause = cls(
            text=data.get("text", ""),
            clause_id=data.get("id"), # Will generate new if None
            jurisdiction=data.get("jurisdiction", "Lex Aequies"),
            origin=data.get("origin", "User Input")
        )
        # Preserve original creation/modification dates and version if available
        clause.creation_date = data.get("creation_date", clause.creation_date)
        clause.last_modified_date = data.get("last_modified_date", clause.last_modified_date)
        clause.version = data.get("version", clause.version)
        clause.metadata = data.get("metadata", {})

        # If ID was explicitly None and a new one was generated, but data had an ID, prefer data's ID.
        # This handles the case where clause_id might be passed as None to constructor but exists in data.
        if data.get("id") and clause.id != data.get("id"):
             clause.id = data.get("id")

        return clause

if __name__ == '__main__':
    clause1 = Clause(text="This is the first primary clause of the trust.", jurisdiction="Lex Aequies")
    print(clause1)
    print(clause1.to_dict())

    clause2_data = {
        "id": "CL-CUSTOM123",
        "text": "All conveyance under this charter is subject to Lex Postalis.",
        "jurisdiction": "Lex Postalis",
        "origin": "Template",
        "creation_date": "2023-01-01T10:00:00",
        "last_modified_date": "2023-01-02T11:00:00",
        "version": 2,
        "metadata": {"source_doc_id": "CHARTER_TEMPLATE_V1"}
    }
    clause2 = Clause.from_dict(clause2_data)
    print(clause2)
    print(clause2.to_dict())

    assert clause2.id == "CL-CUSTOM123"
    assert clause2.metadata["source_doc_id"] == "CHARTER_TEMPLATE_V1"

    clause3 = Clause(text="This special deposit converts the legal fiction into a private equitable asset.")
    clause3.update_jurisdiction("Lex Naturalis")
    print(clause3)
    print(clause3.to_dict())
