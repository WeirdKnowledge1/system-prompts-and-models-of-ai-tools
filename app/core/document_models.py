import uuid
import datetime
from .clause_model import Clause
from .ledger_models import DocumentLedger # Import DocumentLedger

class BaseDocument:
    """
    Base class for all documents in the Michaud Postal Equity App.
    """
    def __init__(self, name: str, doc_type: str):
        self.id = str(uuid.uuid4()) # This ID should be unique per document instance
        self.name = name
        self.doc_type = doc_type
        self.creation_date = datetime.datetime.now().isoformat()
        self.last_modified_date = self.creation_date
        self.jurisdiction = "Lex Aequies" # Default, can be changed
        self.master_ai_concept = "Postal Equity App Core AI" # Placeholder concept
        self.clauses: list[Clause] = []
        self.version = 1
        self.metadata = {}
        self.ledger: DocumentLedger | None = None # Initialize ledger, can also be new DocumentLedger(self.id)

    def get_or_create_ledger(self) -> DocumentLedger:
        """Ensures a ledger exists for this document and returns it."""
        if self.ledger is None:
            self.ledger = DocumentLedger(document_id=self.id)
            # Optionally, add an initial system entry
            # self.ledger.add_entry(title="Document Created", entry_type="System", jurisdiction_tag=self.jurisdiction)
        # Ensure ledger's document_id is synced if self.id changed (e.g. after Save As)
        if self.ledger.document_id != self.id:
            self.ledger.document_id = self.id
        return self.ledger

    def add_clause(self, clause_text: str, clause_id: str = None,
                   jurisdiction: str = None, origin: str = "User Input"):
        """Adds a new Clause object to the document."""
        if jurisdiction is None:
            jurisdiction = self.jurisdiction # Default to document's jurisdiction

        new_clause = Clause(text=clause_text, clause_id=clause_id,
                            jurisdiction=jurisdiction, origin=origin)
        self.clauses.append(new_clause)
        self.last_modified_date = datetime.datetime.now().isoformat()
        self.version += 1
        return new_clause # Return the created clause object

    def update_metadata(self, key: str, value: any):
        self.metadata[key] = value
        self.last_modified_date = datetime.datetime.now().isoformat()

    def to_dict(self):
        """Serializes the document to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "doc_type": self.doc_type,
            "creation_date": self.creation_date,
            "last_modified_date": self.last_modified_date,
            "jurisdiction": self.jurisdiction,
            "master_ai_concept": self.master_ai_concept,
            "clauses": [clause.to_dict() for clause in self.clauses],
            "version": self.version,
            "metadata": self.metadata,
            "ledger": self.ledger.to_dict() if self.ledger else None, # Serialize ledger
            # Specific fields from subclasses will be added here
        }

    @classmethod
    def from_dict(cls, data: dict, instance=None):
        """
        Populates a document instance (or a new one if instance is None)
        from a dictionary. This method is intended to be called by subclasses
        after they have instantiated themselves.
        If instance is provided, it populates that instance.
        Otherwise, it creates a new instance of 'cls' (which should be BaseDocument
        if called directly on BaseDocument, or the specific subclass if that subclass's
        from_dict called super correctly).
        """
        if instance is None:
            # This path is taken if BaseDocument.from_dict is called directly
            # or if a subclass doesn't provide an instance.
            # We need to determine the correct type to instantiate.
            doc_type_from_data = data.get("doc_type")
            if cls == BaseDocument: # If called on BaseDocument itself
                if doc_type_from_data == MichaudFamilyTrust.DOC_TYPE_NAME:
                    doc = MichaudFamilyTrust(name=data.get("name", "Untitled Trust"))
                elif doc_type_from_data == MichaudFamilyPostalCharter.DOC_TYPE_NAME:
                    doc = MichaudFamilyPostalCharter(name=data.get("name", "Untitled Charter"))
                elif doc_type_from_data == MichaudSpecialDepositDocument.DOC_TYPE_NAME:
                    doc = MichaudSpecialDepositDocument(name=data.get("name", "Untitled Deposit"))
                else: # Unknown type or base type requested
                    doc = cls(name=data.get("name", "Untitled Document"),
                              doc_type=doc_type_from_data or "BaseDocument")
            else: # If called via super() from a subclass's from_dict, cls is BaseDocument
                  # but we should have received an instance. If not, this is unusual.
                  # For safety, create instance of current cls, though this might be BaseDocument
                  # if super() wasn't used as expected.
                  # The correct pattern is Subclass.from_dict creates instance, then calls super().from_dict(data, instance=doc)
                doc = cls(name=data.get("name", "Untitled Document"),
                          doc_type=data.get("doc_type", "BaseDocument"))
        else:
            doc = instance

        # Populate base fields
        doc.id = data.get("id", doc.id if hasattr(doc, 'id') and doc.id else str(uuid.uuid4()))
        # Name and doc_type should have been set by the constructor of 'doc'
        doc.name = data.get("name", doc.name)
        doc.doc_type = data.get("doc_type", doc.doc_type)

        doc.creation_date = data.get("creation_date", datetime.datetime.now().isoformat())
        doc.last_modified_date = data.get("last_modified_date", doc.creation_date)
        doc.jurisdiction = data.get("jurisdiction", "Lex Aequies")
        doc.master_ai_concept = data.get("master_ai_concept", "Postal Equity App Core AI")

        doc.clauses = [Clause.from_dict(c_data) for c_data in data.get("clauses", [])]

        doc.version = data.get("version", 1)
        doc.metadata = data.get("metadata", {})

        ledger_data = data.get("ledger")
        if ledger_data:
            # Pass the document's current ID to ensure ledger is associated correctly,
            # especially if the document ID was just (re)generated.
            doc.ledger = DocumentLedger.from_dict(ledger_data, document_id_override=doc.id)
        else:
            # Optionally create a new empty ledger if none in data, or leave as None
            doc.ledger = DocumentLedger(document_id=doc.id) # Ensure new docs get a ledger

        return doc


class MichaudFamilyTrust(BaseDocument):
    """
    Represents the Michaud Family Trust document.
    Part II.A - Michaud Family Trust
    """
    DOC_TYPE_NAME = "Michaud Family Trust"

    def __init__(self, name: str):
        super().__init__(name=name, doc_type=self.DOC_TYPE_NAME)
        self.jurisdiction = "Lex Aequies" # Primary
        self.settlors = [] # List of strings or dicts with details
        self.trustees = [] # List of strings or dicts with details
        self.beneficiaries = [] # List of strings or dicts with details
        self.support_allodial_dominion = True # Example specific field
        self.land_rights_details = ""
        self.name_control_details = ""
        self.equitable_mortgage_reconciliation_details = ""
        # References to Postal Charter and Special Deposit will be by ID or path
        self.postal_charter_ref = None
        self.special_deposit_ref = None

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "settlors": self.settlors,
            "trustees": self.trustees,
            "beneficiaries": self.beneficiaries,
            "support_allodial_dominion": self.support_allodial_dominion,
            "land_rights_details": self.land_rights_details,
            "name_control_details": self.name_control_details,
            "equitable_mortgage_reconciliation_details": self.equitable_mortgage_reconciliation_details,
            "postal_charter_ref": self.postal_charter_ref,
            "special_deposit_ref": self.special_deposit_ref,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict):
        # 1. Create an instance of MichaudFamilyTrust
        doc = cls(name=data.get("name", "Untitled Trust"))

        # 2. Populate base fields using BaseDocument.from_dict, passing the instance
        #    super() here refers to BaseDocument
        doc = super(MichaudFamilyTrust, cls).from_dict(data, instance=doc)

        # 3. Populate MichaudFamilyTrust-specific fields
        #    No need for isinstance check if super().from_dict guarantees returning the passed instance
        doc.settlors = data.get("settlors", [])
        doc.trustees = data.get("trustees", [])
        doc.beneficiaries = data.get("beneficiaries", [])
        doc.support_allodial_dominion = data.get("support_allodial_dominion", True)
        doc.land_rights_details = data.get("land_rights_details", "")
        doc.name_control_details = data.get("name_control_details", "")
        doc.equitable_mortgage_reconciliation_details = data.get("equitable_mortgage_reconciliation_details", "")
        doc.postal_charter_ref = data.get("postal_charter_ref")
        doc.special_deposit_ref = data.get("special_deposit_ref")
        return doc


class MichaudFamilyPostalCharter(BaseDocument):
    """
    Represents the Michaud Family Postal Charter document.
    Part II.A - Michaud Family Postal Charter
    """
    DOC_TYPE_NAME = "Michaud Family Postal Charter"

    def __init__(self, name: str):
        super().__init__(name=name, doc_type=self.DOC_TYPE_NAME)
        self.jurisdiction = "Lex Postalis" # Primary
        self.upu_recognized_format_details = ""
        self.global_upu_tracking_number_fields = "" # Placeholder for actual fields
        self.canada_post_format_compliance_details = ""
        self.usps_format_compliance_details = ""
        self.vienna_convention_reference_details = ""
        self.postal_treaty_law_reference_details = ""
        self.family_trust_ref = None
        self.upu_tracking_number: str | None = None
        self.jurisdictional_delivery_tag: str | None = None

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "upu_recognized_format_details": self.upu_recognized_format_details,
            "global_upu_tracking_number_fields": self.global_upu_tracking_number_fields,
            "canada_post_format_compliance_details": self.canada_post_format_compliance_details,
            "usps_format_compliance_details": self.usps_format_compliance_details,
            "vienna_convention_reference_details": self.vienna_convention_reference_details,
            "postal_treaty_law_reference_details": self.postal_treaty_law_reference_details,
            "family_trust_ref": self.family_trust_ref,
            "upu_tracking_number": self.upu_tracking_number,
            "jurisdictional_delivery_tag": self.jurisdictional_delivery_tag,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict):
        doc = cls(name=data.get("name", "Untitled Charter"))
        doc = super(MichaudFamilyPostalCharter, cls).from_dict(data, instance=doc)

        doc.upu_recognized_format_details = data.get("upu_recognized_format_details", "")
        doc.global_upu_tracking_number_fields = data.get("global_upu_tracking_number_fields", "")
        doc.canada_post_format_compliance_details = data.get("canada_post_format_compliance_details", "")
        doc.usps_format_compliance_details = data.get("usps_format_compliance_details", "")
        doc.vienna_convention_reference_details = data.get("vienna_convention_reference_details", "")
        doc.postal_treaty_law_reference_details = data.get("postal_treaty_law_reference_details", "")
        doc.family_trust_ref = data.get("family_trust_ref")
            doc.upu_tracking_number = data.get("upu_tracking_number")
            doc.jurisdictional_delivery_tag = data.get("jurisdictional_delivery_tag")
        return doc

class MichaudSpecialDepositDocument(BaseDocument):
    """
    Represents the Michaud Special Deposit Document.
    Part II.A - Special Deposit Document
    """
    DOC_TYPE_NAME = "Michaud Special Deposit Document"

    def __init__(self, name: str):
        super().__init__(name=name, doc_type=self.DOC_TYPE_NAME)
        self.jurisdiction = "Lex Aequies" # Primary, with Lex Postalis elements
        self.filed_documents = [] # E.g., {"doc_name": "Birth Certificate", "details": "BC12345"}
        self.source_validation_details = "" # E.g., "Lifted seal, barcode verified"
        self.trust_beneficiary_alignment_notes = ""
        self.postal_equity_agent_signature_placeholder = ""
        self.notary_signature_placeholder = ""
        # References
        self.family_trust_ref = None
        self.postal_charter_ref = None
        # Legal jurisdictional citations (examples)
        self.foreign_trustee_act_citation = ""
        self.subrogate_practice_act_citation = ""
        self.manitoba_statutes_special_deposit_citation = ""
        self.upu_tracking_number: str | None = None
        self.jurisdictional_delivery_tag: str | None = None


    def to_dict(self):
        data = super().to_dict()
        data.update({
            "filed_documents": self.filed_documents,
            "source_validation_details": self.source_validation_details,
            "trust_beneficiary_alignment_notes": self.trust_beneficiary_alignment_notes,
            "postal_equity_agent_signature_placeholder": self.postal_equity_agent_signature_placeholder,
            "notary_signature_placeholder": self.notary_signature_placeholder,
            "family_trust_ref": self.family_trust_ref,
            "postal_charter_ref": self.postal_charter_ref,
            "foreign_trustee_act_citation": self.foreign_trustee_act_citation,
            "subrogate_practice_act_citation": self.subrogate_practice_act_citation,
            "manitoba_statutes_special_deposit_citation": self.manitoba_statutes_special_deposit_citation,
            "upu_tracking_number": self.upu_tracking_number,
            "jurisdictional_delivery_tag": self.jurisdictional_delivery_tag,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict):
        doc = cls(name=data.get("name", "Untitled Deposit"))
        doc = super(MichaudSpecialDepositDocument, cls).from_dict(data, instance=doc)

        doc.filed_documents = data.get("filed_documents", [])
        doc.source_validation_details = data.get("source_validation_details", "")
        doc.trust_beneficiary_alignment_notes = data.get("trust_beneficiary_alignment_notes", "")
        doc.postal_equity_agent_signature_placeholder = data.get("postal_equity_agent_signature_placeholder", "")
        doc.notary_signature_placeholder = data.get("notary_signature_placeholder", "")
        doc.family_trust_ref = data.get("family_trust_ref")
        doc.postal_charter_ref = data.get("postal_charter_ref")
        doc.foreign_trustee_act_citation = data.get("foreign_trustee_act_citation", "")
        doc.subrogate_practice_act_citation = data.get("subrogate_practice_act_citation", "")
        doc.manitoba_statutes_special_deposit_citation = data.get("manitoba_statutes_special_deposit_citation", "")
        doc.upu_tracking_number = data.get("upu_tracking_number")
        doc.jurisdictional_delivery_tag = data.get("jurisdictional_delivery_tag")
        return doc

# Example Usage (for testing, not part of the final app logic here)
if __name__ == "__main__":
    trust_doc = MichaudFamilyTrust(name="Rene Michaud Family Trust Main")
    trust_doc.settlors.append("Rene Michaud")
    trust_doc.trustees.append("Louise Michaud")
    trust_doc.beneficiaries.append("Family Lineage")
    trust_doc.add_clause("This is the first principal clause of the trust.", "TRUST-001", "Lex Aequies")

    print("Trust Document Created:")
    print(f"ID: {trust_doc.id}")
    print(f"Name: {trust_doc.name}")
    print(f"Type: {trust_doc.doc_type}")
    print(f"Jurisdiction: {trust_doc.jurisdiction}")
    print(f"Settlors: {trust_doc.settlors}")
    print(f"Clauses: {trust_doc.clauses}")
    print("-" * 20)

    charter_doc = MichaudFamilyPostalCharter(name="Michaud Postal Charter Alpha")
    charter_doc.upu_recognized_format_details = "Compliant with UPU S42 standard."
    charter_doc.add_clause("All conveyance under this charter is subject to Lex Postalis.", "CHARTER-001", "Lex Postalis")
    print("Charter Document Created:")
    print(f"ID: {charter_doc.id}")
    print(f"Name: {charter_doc.name}")
    print(f"Jurisdiction: {charter_doc.jurisdiction}")
    print(f"UPU Details: {charter_doc.upu_recognized_format_details}")
    print(f"Clauses: {charter_doc.clauses}")
    print("-" * 20)

    deposit_doc = MichaudSpecialDepositDocument(name="Initial Special Deposit - BC Rene")
    deposit_doc.filed_documents.append({"doc_name": "Birth Certificate - Rene Michaud", "id": "BC-RM-1970"})
    deposit_doc.add_clause("This special deposit converts the legal fiction into a private equitable asset.", "DEPOSIT-001")
    print("Special Deposit Document Created:")
    print(f"ID: {deposit_doc.id}")
    print(f"Name: {deposit_doc.name}")
    print(f"Filed Docs: {deposit_doc.filed_documents}")
    print(f"Clauses: {deposit_doc.clauses}")

    print("\nSerialization/Deserialization Test:")
    trust_dict = trust_doc.to_dict()
    reloaded_trust = MichaudFamilyTrust.from_dict(trust_dict)
    assert reloaded_trust.id == trust_doc.id
    assert reloaded_trust.name == trust_doc.name
    assert reloaded_trust.settlors == trust_doc.settlors
    assert len(reloaded_trust.clauses) == len(trust_doc.clauses)
    print("Trust Reloaded Successfully.")

    charter_dict = charter_doc.to_dict()
    reloaded_charter = MichaudFamilyPostalCharter.from_dict(charter_dict)
    assert reloaded_charter.id == charter_doc.id
    assert reloaded_charter.upu_recognized_format_details == charter_doc.upu_recognized_format_details
    print("Charter Reloaded Successfully.")

    deposit_dict = deposit_doc.to_dict()
    reloaded_deposit = MichaudSpecialDepositDocument.from_dict(deposit_dict)
    assert reloaded_deposit.id == deposit_doc.id
    assert len(reloaded_deposit.filed_documents) == len(deposit_doc.filed_documents)
    print("Deposit Reloaded Successfully.")
