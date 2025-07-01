import uuid
import datetime

class BaseDocument:
    """
    Base class for all documents in the Michaud Postal Equity App.
    """
    def __init__(self, name: str, doc_type: str):
        self.id = str(uuid.uuid4())
        self.name = name  # Specific name of the document instance, e.g., "Rene Michaud Family Trust 2024"
        self.doc_type = doc_type # e.g., DOC_TRUST, DOC_CHARTER
        self.creation_date = datetime.datetime.now().isoformat()
        self.last_modified_date = self.creation_date
        self.jurisdiction = "Lex Aequies" # Default, can be changed
        self.master_ai_concept = "Postal Equity App Core AI" # Placeholder concept
        self.clauses = [] # Will hold Clause objects
        self.version = 1
        self.metadata = {} # For any additional, non-structured data

    def add_clause(self, clause_text: str, clause_id: str = None, jurisdiction: str = None):
        # This is a placeholder for now. Proper Clause object will be used later.
        # from .clause_model import Clause # Avoid circular import for now
        # clause = Clause(text=clause_text, clause_id=clause_id, jurisdiction=jurisdiction)
        # self.clauses.append(clause)
        # For now, just storing text.
        self.clauses.append({"id": clause_id or str(uuid.uuid4()), "text": clause_text, "jurisdiction": jurisdiction or self.jurisdiction})
        self.last_modified_date = datetime.datetime.now().isoformat()
        self.version += 1

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
            "clauses": self.clauses, # In Phase 1, clauses are simple dicts
            "version": self.version,
            "metadata": self.metadata,
            # Specific fields from subclasses will be added here
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserializes the document from a dictionary."""
        # This is a generic loader. Subclasses should override for specific fields.
        doc_type = data.get("doc_type")
        if doc_type == "Michaud Family Trust":
            doc = MichaudFamilyTrust(name=data.get("name", "Untitled Trust"))
        elif doc_type == "Michaud Family Postal Charter":
            doc = MichaudFamilyPostalCharter(name=data.get("name", "Untitled Charter"))
        elif doc_type == "Michaud Special Deposit Document":
            doc = MichaudSpecialDepositDocument(name=data.get("name", "Untitled Deposit"))
        else:
            # Fallback or raise error
            doc = cls(name=data.get("name", "Untitled Document"), doc_type=doc_type)

        doc.id = data.get("id", str(uuid.uuid4()))
        doc.creation_date = data.get("creation_date", datetime.datetime.now().isoformat())
        doc.last_modified_date = data.get("last_modified_date", doc.creation_date)
        doc.jurisdiction = data.get("jurisdiction", "Lex Aequies")
        doc.master_ai_concept = data.get("master_ai_concept", "Postal Equity App Core AI")
        doc.clauses = data.get("clauses", []) # In Phase 1, clauses are simple dicts
        doc.version = data.get("version", 1)
        doc.metadata = data.get("metadata", {})
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
        doc = super().from_dict(data) # This will call the correct class constructor via cls()
        if isinstance(doc, MichaudFamilyTrust): # Ensure we got the right type
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
        self.family_trust_ref = None # Reference to the Family Trust

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
        })
        return data

    @classmethod
    def from_dict(cls, data: dict):
        doc = super().from_dict(data)
        if isinstance(doc, MichaudFamilyPostalCharter):
            doc.upu_recognized_format_details = data.get("upu_recognized_format_details", "")
            doc.global_upu_tracking_number_fields = data.get("global_upu_tracking_number_fields", "")
            doc.canada_post_format_compliance_details = data.get("canada_post_format_compliance_details", "")
            doc.usps_format_compliance_details = data.get("usps_format_compliance_details", "")
            doc.vienna_convention_reference_details = data.get("vienna_convention_reference_details", "")
            doc.postal_treaty_law_reference_details = data.get("postal_treaty_law_reference_details", "")
            doc.family_trust_ref = data.get("family_trust_ref")
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
        })
        return data

    @classmethod
    def from_dict(cls, data: dict):
        doc = super().from_dict(data)
        if isinstance(doc, MichaudSpecialDepositDocument):
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
