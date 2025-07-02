# Placeholder classes for AI Agent Infrastructure (Part II.B)
import qrcode
import io
from PyQt6.QtGui import QPixmap, QImage
import os
import datetime
import re # For regex-based cross-reference search
import shutil # For file copying in AutoBackup
import json # For VeritasProof proof object
import hashlib # For hashing clause text in VeritasProof

from app.core.document_utils import generate_display_clause_numbers # Import for numbering checks
# Need Clause type hint for VeritasProof
from app.core.clause_model import Clause
# For semantic similarity in ClauseConformer
from app.core.nlp_utils import calculate_tfidf_cosine_similarity, SKLEARN_AVAILABLE

class BaseAgent:
    """
    Base class for all AI agents in the Michaud Postal Equity App.
    """
    def __init__(self, agent_name: str, app_context=None):
        self.agent_name = agent_name
        self.app_context = app_context # To access shared resources, settings, documents etc.
        self.status = "Idle"
        self.last_error = None
        print(f"Agent Initialized: {self.agent_name}")

    def get_status(self):
        return {"name": self.agent_name, "status": self.status, "last_error": self.last_error}

    def log_error(self, error_message: str):
        self.last_error = error_message
        self.status = "Error"
        print(f"ERROR in {self.agent_name}: {error_message}")

    def set_status(self, new_status: str):
        self.status = new_status
        print(f"STATUS of {self.agent_name}: {new_status}")


class PostalEquityAppAI(BaseAgent):
    """
    The Sentient Master AI. This is the app.
    Capable of interpreting, generating, and validating legal content.
    """
    def __init__(self, app_context=None):
        super().__init__(agent_name="Postal Equity App (Master AI)", app_context=app_context)
        # This agent would have access to all other agents and document models.

    def interpret_command(self, command: str, context_document=None):
        self.set_status(f"Interpreting command: {command}")
        command_lower = command.lower()
        response_message = f"Command '{command}' processed." # Default response

        # Ensure app_context and dashboard_view are available for notifications
        dashboard_view = None
        if self.app_context and hasattr(self.app_context, 'dashboard_view'):
            dashboard_view = self.app_context.dashboard_view

        def add_dashboard_notification(message):
            if dashboard_view and hasattr(dashboard_view, 'add_notification'):
                dashboard_view.add_notification(f"MasterAI: {message}")
            else:
                print(f"MasterAI Notification (no dashboard): {message}")

        if "validate" in command_lower or "check conformity" in command_lower or "conform" in command_lower:
            if context_document:
                add_dashboard_notification(f"Initiating conformance check for document: {context_document.name}")
                try:
                    conformer = ClauseConformer(app_context=self.app_context)
                    # Ensure the document object has its data collected if it's from a view
                    # This might require the view to have a method like `get_current_document_data_for_agent`
                    # For now, assume context_document is up-to-date.
                    # If the document view has `_collect_data_from_ui`, it should be called before this.
                    # The `_send_command_to_master_ai` in DashboardView tries to pass active_doc_view.document
                    # We assume this document object is sufficiently current.

                    issues = conformer.check_document_for_basic_issues(context_document)

                    if issues:
                        summary = f"Conformance check for '{context_document.name}' found {len(issues)} issue(s)."
                        add_dashboard_notification(summary)
                        for i, issue_item in enumerate(issues):
                            issue_prefix = f"  Issue {i+1}: "
                            issue_text = issue_item.get('issue', 'No details')
                            severity = issue_item.get('severity', 'N/A')

                            # Handle different ID structures
                            id_info = ""
                            if issue_item.get('type') == "semantic_similarity":
                                ids_involved = issue_item.get('ids', [])
                                id_info = f"(Involves IDs: {', '.join([id_val[:8] + '...' for id_val in ids_involved])})"
                            else:
                                id_info = f"(ID: {issue_item.get('id', 'N/A')[:10]}...)"

                            issue_msg = f"{issue_prefix}{issue_text} (Severity: {severity}) {id_info}"

                            if "suggestions" in issue_item and issue_item["suggestions"]:
                                issue_msg += "\n    Suggestions:"
                                for sugg in issue_item["suggestions"]:
                                    issue_msg += f"\n      - {sugg}"
                            add_dashboard_notification(issue_msg)
                        response_message = summary + " See dashboard notifications for details."
                    else:
                        summary = f"No conformance issues found in '{context_document.name}'."
                        add_dashboard_notification(summary)
                        response_message = summary
                except Exception as e:
                    error_msg = f"Error during conformance check: {e}"
                    add_dashboard_notification(error_msg)
                    response_message = error_msg
            else:
                no_doc_msg = "No active document context to validate. Please open or select a document."
                add_dashboard_notification(no_doc_msg)
                response_message = no_doc_msg

        elif "help" in command_lower:
            response_message = "Available commands:\n" \
                               "- 'validate current document' / 'check conformity': Runs conformance check on active document.\n" \
                               "- 'help': Shows this help message."
            add_dashboard_notification("Displaying help for Master AI commands.")
            # For more complex help, could return a structured object or specific UI update signal.

        elif command_lower.startswith("search law library for ") or command_lower.startswith("find in library "):
            search_term = ""
            if command_lower.startswith("search law library for "):
                search_term = command.split("search law library for ", 1)[1].strip()
            elif command_lower.startswith("find in library "):
                search_term = command.split("find in library ", 1)[1].strip()

            if search_term:
                if self.app_context and hasattr(self.app_context, 'law_library_view') and \
                   hasattr(self.app_context.law_library_view, 'perform_search'):

                    # Switch to the Law Library tab
                    if hasattr(self.app_context, 'tab_widget') and hasattr(self.app_context, 'law_library_view'):
                        try:
                            law_lib_tab_index = -1
                            for i in range(self.app_context.tab_widget.count()):
                                if self.app_context.tab_widget.widget(i) == self.app_context.law_library_view:
                                    law_lib_tab_index = i
                                    break
                            if law_lib_tab_index != -1:
                                self.app_context.tab_widget.setCurrentIndex(law_lib_tab_index)
                            else:
                                add_dashboard_notification("Could not find Law Library tab to switch to.")
                        except Exception as e_tab:
                             add_dashboard_notification(f"Error switching to Law Library tab: {e_tab}")

                    self.app_context.law_library_view.perform_search(search_term)
                    msg = f"Law Library search for '{search_term}' initiated. Check the 'Law Library & Codex' tab."
                    add_dashboard_notification(msg)
                    response_message = msg
                else:
                    no_view_msg = "Law Library view or search function not available."
                    add_dashboard_notification(no_view_msg)
                    response_message = no_view_msg
            else:
                no_term_msg = "No search term provided for Law Library search."
                add_dashboard_notification(no_term_msg)
                response_message = no_term_msg

        else:
            unrec_msg = f"Unrecognized command: '{command}'. Type 'help' for available commands."
            add_dashboard_notification(unrec_msg)
            response_message = unrec_msg

        self.set_status("Idle")
        # The DashboardView's _send_command_to_master_ai method will also add this response if returned.
        # It's fine if it's a bit redundant for now, or one could be prioritized.
        # Returning None here would mean only notifications posted by MasterAI itself appear.
        return response_message


    def rewrite_own_logic_from_zip(self, zip_path: str):
        self.set_status(f"Attempting to rewrite logic from ZIP: {zip_path}")
        # Placeholder for complex ZIP module loading and self-modification
        print(f"{self.agent_name}: Logic rewrite from ZIP module '{zip_path}' initiated. (Placeholder)")
        # This would involve security checks, parsing, and dynamic code loading/replacement.
        self.set_status("Idle")
        return True # Or False on failure

    def convert_ecclesiastical_clause(self, clause_text: str, target_jurisdiction="Lex Triad"):
        self.set_status(f"Converting ecclesiastical clause to {target_jurisdiction}")
        # Placeholder for clause conversion logic
        converted_text = f"[Converted to {target_jurisdiction}] {clause_text} (Placeholder)"
        print(f"{self.agent_name}: Clause converted. Original: '{clause_text}', New: '{converted_text}'")
        self.set_status("Idle")
        return converted_text

class ClauseConformer(BaseAgent):
    """
    Compares documents, detects inconsistencies, and harmonizes them.
    """
    def __init__(self, app_context=None):
        super().__init__(agent_name="ClauseConformer", app_context=app_context)

    def harmonize_documents(self, documents: list):
        self.set_status(f"Harmonizing {len(documents)} documents.")
        if not documents or len(documents) < 2:
            self.log_error("At least two documents are required for harmonization.")
            return None

        # Placeholder: Detailed logic for clause comparison, conflict detection, and resolution
        print(f"{self.agent_name}: Comparing and harmonizing clauses across provided documents. (Placeholder)")
        # This agent would analyze clause IDs, text, jurisdiction, and structural position.
        # It would generate a report of inconsistencies and proposed changes.
        harmonization_report = {"conflicts_found": 0, "changes_proposed": 0, "status": "Simulated"}
        self.set_status("Idle")
        return harmonization_report

    def check_document_for_basic_issues(self, document_obj) -> list[str]:
        """
        Performs basic conceptual checks on a single document object.
        Returns a list of issue strings.
        """
        if not document_obj:
            return ["No document provided for conformance check."]

        self.set_status(f"Running basic conformance check on: {document_obj.name} ({document_obj.doc_type})")
        issues_report = [] # List of issue dictionaries

        # Check 1: Empty clause text
        for i, clause in enumerate(document_obj.clauses):
            if not clause.text.strip():
                issues_report.append({
                    "id": clause.id,
                    "issue": f"Clause {i+1} has empty text.",
                    "severity": "warning",
                    "suggestions": [
                        "Provide the full intended text for this clause.",
                        "If this clause is no longer needed, consider deleting it."
                    ]
                })
            # Check 2: Clause length (new)
            elif len(clause.text.strip()) < 10:
                 issues_report.append({
                    "id": clause.id,
                    "issue": f"Clause {i+1} text is very short ({len(clause.text.strip())} chars). Review for completeness.",
                    "severity": "info",
                    "suggestions": [
                        "Ensure the clause text adequately covers its intended purpose.",
                        "Consider expanding the clause for clarity or legal sufficiency."
                    ]
                })
            elif len(clause.text.strip()) > 1000: # Example length, can be configured
                 issues_report.append({
                    "id": clause.id,
                    "issue": f"Clause {i+1} text is very long ({len(clause.text.strip())} chars). Review for conciseness.",
                    "severity": "info",
                    "suggestions": [
                        "Review for conciseness and clarity. Can it be broken down?",
                        "Ensure there is no redundant information."
                    ]
                })


        # Check 3: Basic jurisdictional mix (previously check 2)
        expected_jurisdictions = {
            "Michaud Family Trust": "Lex Aequies",
            "Michaud Special Deposit Document": "Lex Aequies", # Can also have Postal elements, but primary is Aequies
            "Michaud Family Postal Charter": "Lex Postalis"
        }

        doc_primary_jurisdiction = document_obj.jurisdiction
        doc_expected_primary = expected_jurisdictions.get(document_obj.doc_type)

        if doc_expected_primary and doc_primary_jurisdiction != doc_expected_primary:
            issues_report.append({
                "id": document_obj.id, # Document level issue
                "issue": f"Document's declared jurisdiction ('{doc_primary_jurisdiction}') "
                         f"differs from typical primary for its type ('{doc_expected_primary}').",
                "severity": "warning"
            })

        for i, clause in enumerate(document_obj.clauses):
            clause_issue_prefix = f"Clause {i+1} (ID: {clause.id})"

            # Check for jurisdictional mix based on document type
            if document_obj.doc_type in ["Michaud Family Trust", "Michaud Special Deposit Document"]:
                if clause.jurisdiction == "Lex Postalis":
                    issues_report.append({
                        "id": clause.id,
                        "issue": f"{clause_issue_prefix} in a '{document_obj.doc_type}' (typically Lex Aequies) "
                                 f"has 'Lex Postalis' jurisdiction. Review for intended use.",
                        "severity": "info"
                    })
            elif document_obj.doc_type == "Michaud Family Postal Charter":
                if clause.jurisdiction == "Lex Aequies":
                    issues_report.append({
                        "id": clause.id,
                        "issue": f"{clause_issue_prefix} in a 'Michaud Family Postal Charter' (typically Lex Postalis) "
                                 f"has 'Lex Aequies' jurisdiction. Review for intended use.",
                        "severity": "info"
                    })

            # General check for unusual jurisdictions not matching document's or main triad
            # (unless it's the document's own declared jurisdiction, which might be non-standard but intentional)
            if clause.jurisdiction != document_obj.jurisdiction and \
               clause.jurisdiction not in ["Lex Aequies", "Lex Postalis", "Lex Naturalis"]:
                issues_report.append({
                    "id": clause.id,
                    "issue": f"{clause_issue_prefix} has an unusual jurisdiction ('{clause.jurisdiction}') "
                             f"that does not match the document's declared jurisdiction ('{document_obj.jurisdiction}') "
                             f"or the primary Lex Triad. Requires review.",
                    "severity": "info"
                })

        # New Check 4: Numbering Consistency (using generate_display_clause_numbers)
        if document_obj.clauses:
            try:
                display_numbers = generate_display_clause_numbers(document_obj.clauses)
                seen_numbers = set()
                for i, num_str in enumerate(display_numbers):
                    clause_id_for_issue = document_obj.clauses[i].id if i < len(document_obj.clauses) else document_obj.id
                    if "Err!" in num_str: # Error from numbering function
                        issues_report.append({
                            "id": clause_id_for_issue,
                            "issue": f"Clause {i+1} (or around it) has a numbering generation error: '{num_str}'. Review clause levels/titles.",
                            "severity": "warning"
                        })
                    # Basic duplicate check for generated numbers (excluding errors and simple section titles that might not be unique)
                    if num_str not in seen_numbers and not num_str.startswith("SECTION") and not re.match(r"^[A-Z]\.\s", num_str) :
                        seen_numbers.add(num_str)
                    elif num_str in seen_numbers and num_str != "Err!" and not num_str.startswith("SECTION") and not re.match(r"^[A-Z]\.\s", num_str):
                         issues_report.append({
                            "id": clause_id_for_issue,
                            "issue": f"Duplicate display number '{num_str}' generated for Clause {i+1} (or around it). Check levels/titles.",
                            "severity": "warning"
                        })
                # TODO: More sophisticated sequence logic (e.g., 1.1 then 1.3 without 1.2) is complex and deferred.
            except Exception as e:
                issues_report.append({ "id": document_obj.id, "issue": f"Error during clause number generation for checks: {e}", "severity": "error"})

        # New Check 5: Placeholder Cross-Reference Text Search
        cross_ref_patterns = [
            r"See Clause\s+[\w\.]+", r"Refers to Section\s+[\w\.]+",
            r"Article\s+[\w\.]+", r"as per paragraph\s+[\w\.]+",
            r"pursuant to section\s+[\w\.]+" # Added another common pattern
        ]
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in cross_ref_patterns]

        for i, clause in enumerate(document_obj.clauses):
            for pattern in compiled_patterns:
                if pattern.search(clause.text):
                    issues_report.append({
                        "id": clause.id,
                        "issue": f"Clause {i+1} (ID: {clause.id}) may contain a text-based cross-reference. Manual verification of target and number accuracy needed.",
                        "severity": "info"
                    })
                    break # Only report one type of cross-ref finding per clause for this basic check

        # New Check 6: Semantic Similarity between clauses in the same document
        if SKLEARN_AVAILABLE and document_obj.clauses and len(document_obj.clauses) >= 2:
            # Create a list of (clause_id, clause_text, display_number_if_available)
            # Display numbers are helpful for user reporting
            clause_texts_with_ids = []
            display_numbers_for_similarity = generate_display_clause_numbers(document_obj.clauses) # Get once
            for idx, c_obj in enumerate(document_obj.clauses):
                # Use display number if possible, otherwise index for reference in message
                ref_label = display_numbers_for_similarity[idx] if idx < len(display_numbers_for_similarity) else f"Clause {idx+1}"
                clause_texts_with_ids.append((c_obj.id, c_obj.text, ref_label))

            # Iterate through unique pairs of clauses
            # To avoid redundant checks (A,B) vs (B,A) and self-check (A,A)
            # Also, to avoid multiple reports for the same pair, track reported pairs.
            reported_similar_pairs = set()

            for i in range(len(clause_texts_with_ids)):
                for j in range(i + 1, len(clause_texts_with_ids)):
                    id1, text1, label1 = clause_texts_with_ids[i]
                    id2, text2, label2 = clause_texts_with_ids[j]

                    # Ensure we haven't reported this pair already (e.g. if IDs are sorted)
                    pair_key = tuple(sorted((id1, id2)))
                    if pair_key in reported_similar_pairs:
                        continue

                    # Skip if either text is very short, as TF-IDF might give spurious high scores
                    if len(text1.split()) < 5 or len(text2.split()) < 5: # Min 5 words to compare
                        continue

                    similarity_score = calculate_tfidf_cosine_similarity(text1, text2)

                    # Define a threshold for reporting similarity
                    SIMILARITY_THRESHOLD = 0.85 # Configurable, e.g. 0.85 for reasonably high similarity

                    if similarity_score >= SIMILARITY_THRESHOLD:
                        issues_report.append({
                            "type": "semantic_similarity", # New issue type
                            "ids": [id1, id2], # List of involved clause IDs
                            "issue": f"Clauses '{label1}' (ID: {id1[:8]}...) and '{label2}' (ID: {id2[:8]}...) "
                                     f"are very similar (Score: {similarity_score:.2f}). "
                                     "Consider consolidating or differentiating them.",
                            "severity": "info", # Or 'warning' if threshold is very high
                            "similarity_score": similarity_score,
                            "suggestions": [
                                "Review both clauses to determine if they are redundant.",
                                "If their intent is different, try to rephrase one or both for clarity.",
                                "Consider merging them if they serve the same purpose."
                            ]
                        })
                        reported_similar_pairs.add(pair_key)
        elif not SKLEARN_AVAILABLE and document_obj.clauses and len(document_obj.clauses) >=2 :
            # Add a one-time info message if scikit-learn is not available for this check
            if not any(item.get("type") == "sklearn_missing_for_similarity" for item in issues_report):
                 issues_report.append({
                    "id": document_obj.id, # Document level info
                    "type": "sklearn_missing_for_similarity",
                    "issue": "Semantic similarity check between clauses was skipped because 'scikit-learn' library is not installed.",
                    "severity": "info"
                })


        if not issues_report:
            print(f"{self.agent_name}: No basic issues found in {document_obj.name}.")
        else:
            print(f"{self.agent_name}: Found {len(issues_report)} basic issue(s) in {document_obj.name}.")
            for issue_item in issues_report: # Updated print for potentially new structure
                print(f"  - IDs: {issue_item.get('ids', issue_item.get('id'))}, Type: {issue_item.get('type', 'N/A')}, Severity: {issue_item['severity']}, Issue: {issue_item['issue']}")
                if "suggestions" in issue_item and issue_item["suggestions"]:
                    for sugg in issue_item["suggestions"]: print(f"    Suggestion: {sugg}")

        self.set_status("Idle")
        return issues_report

class CodexSentinel(BaseAgent):
    """
    Meta-auditor. Red-teams system logic, detects drift, and forces healing.
    """
    def __init__(self, app_context=None):
        super().__init__(agent_name="Codex Sentinel", app_context=app_context)

    def perform_system_audit(self):
        self.set_status("Performing system-wide audit.")
        # Placeholder: Logic to scan agent behavior, document integrity, Codex Vault consistency
        print(f"{self.agent_name}: Auditing system logic, agent states, and document consistency. (Placeholder)")
        # Would check for drift, conflicts, and adherence to Lex Triad principles.
        audit_results = {"issues_detected": 0, "recommendations": [], "status": "Simulated"}
        if audit_results["issues_detected"] > 0:
            # self.force_healing_protocol() # Example of a further action
            pass
        self.set_status("Idle")
        return audit_results

    def force_healing_protocol(self):
        self.set_status("Initiating healing protocol.")
        # Placeholder for restoring from backups or known good states
        print(f"{self.agent_name}: Healing protocol initiated. (Placeholder)")
        self.set_status("Idle")


class VeritasProof(BaseAgent):
    """
    Generates QR-authenticated proof chains.
    """
    def __init__(self, app_context=None):
        super().__init__(agent_name="VeritasProof", app_context=app_context)

    def generate_qr_for_text(self, text_data: str) -> QPixmap | None:
        """
        Generates a QR code for the given text_data and returns it as a QPixmap.
        Returns None if generation fails.
        """
        self.set_status(f"Generating QR code for data: {text_data[:30]}...")
        if not text_data:
            self.log_error("No data provided for QR code generation.")
            return None
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10, # Size of each box in the QR grid
                border=4,    # Thickness of the border
            )
            qr.add_data(text_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert PIL image to QPixmap
            buffer = io.BytesIO()
            img.save(buffer, "PNG")
            buffer.seek(0)

            q_image = QImage()
            q_image.loadFromData(buffer.getvalue(), "PNG")
            pixmap = QPixmap.fromImage(q_image)

            self.set_status("Idle")
            print(f"{self.agent_name}: QR code generated successfully for data: {text_data[:30]}...")
            return pixmap
        except Exception as e:
            self.log_error(f"QR code generation failed: {e}")
            return None

    # generate_qr_proof can be a higher-level method that calls generate_qr_for_text
    def generate_qr_proof(self, document_hash: str, timestamp: str, clause_id_map: dict, source_url: str = None) -> QPixmap | None:
        self.set_status("Generating QR proof chain.")
        # For now, let's just make a QR of a combined string of this data
        # In future, this could be a structured format like JSON within the QR
        proof_data_str = f"DocHash: {document_hash}\nTimestamp: {timestamp}\nClauses: {len(clause_id_map)}\nSource: {source_url or 'N/A'}"

        # Limit length for QR code if necessary, or handle larger data appropriately
        # For this example, we'll use the string as is.

        return self.generate_qr_for_text(proof_data_str)

    def generate_clause_proof_qr(self, clause_object: Clause, user_id: int | str | None, doc_id: str | None = None) -> QPixmap | None:
        """
        Generates a QR code containing a JSON proof object for a clause.
        """
        self.set_status(f"Generating proof QR for Clause ID: {clause_object.id}")
        if not clause_object:
            self.log_error("No clause object provided for proof generation.")
            return None

        # 1. Define Proof Object Structure & Construct it
        clause_text_hash = hashlib.sha256(clause_object.text.encode('utf-8')).hexdigest()

        proof_object = {
            "doc_id": doc_id or "UNKNOWN_DOC_ID", # Document ID should ideally be passed or retrieved from clause context
            "clause_id": clause_object.id,
            "clause_text_hash": clause_text_hash, # SHA256 hash of the clause text
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), # UTC timestamp
            "user_id": user_id or "ANONYMOUS", # User ID from login session
            "version": clause_object.version, # Clause version
            "jurisdiction": clause_object.jurisdiction, # Clause jurisdiction
            "origin": clause_object.origin, # Clause origin
            "schema_version": "1.0.0" # Version of this proof object schema
        }

        # 2. Serialize to JSON string
        try:
            json_proof_string = json.dumps(proof_object, sort_keys=True) # Sort keys for consistent hashing if QR itself is hashed
        except TypeError as e:
            self.log_error(f"Could not serialize proof object to JSON: {e}")
            return None

        # 3. Generate QR code for the JSON string
        qr_pixmap = self.generate_qr_for_text(json_proof_string)

        if qr_pixmap:
            self.set_status("Idle - Proof QR generated.")
        else:
            # generate_qr_for_text would have logged its own error
            self.set_status("Error - Proof QR generation failed.")

        return qr_pixmap


class DriftGuard(BaseAgent):
    """
    Monitors the AI itself for simplification, paraphrasing, or token trimming.
    """
    def __init__(self, app_context=None):
        super().__init__(agent_name="DriftGuard", app_context=app_context)

    def check_ai_output_integrity(self, original_intent: str, ai_generated_output: str):
        self.set_status("Checking AI output integrity.")
        # Placeholder: Compare AI output against original intent/source to detect unwanted modifications.
        # This is a complex NLP task.
        drift_detected = False
        if len(ai_generated_output) < len(original_intent) * 0.8: # Simplistic check
            # drift_detected = True # Example
            pass

        print(f"{self.agent_name}: AI output integrity check performed. Drift detected: {drift_detected}. (Placeholder)")
        if drift_detected:
            # self.trigger_rollback() # Example
            return {"drift_detected": True, "report": "Potential summarization detected."}

        self.set_status("Idle")
        return {"drift_detected": False, "report": "Output appears consistent with intent."}

    def trigger_rollback(self, module_name: str = "MasterAI"):
        self.set_status(f"Rollback triggered for module: {module_name}")
        print(f"{self.agent_name}: Rollback of {module_name} to last known good state initiated. (Placeholder)")
        self.set_status("Idle")

class AutoBackup(BaseAgent):
    """
    Saves full Codex memory, user preferences, uploaded files, output docs, and ZIP agents daily.
    """
    def __init__(self, app_context=None):
        super().__init__(agent_name="AutoBackup", app_context=app_context)
        self.backup_location = os.path.join("data", "backups")
        os.makedirs(self.backup_location, exist_ok=True)
        self.data_root_dir = "data" # Base directory for other data files

    def perform_backup(self):
        self.set_status("Performing system backup.")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create a timestamped subdirectory for this specific backup
        current_backup_dir_name = f"mpea_backup_{timestamp}"
        current_backup_path = os.path.join(self.backup_location, current_backup_dir_name)

        try:
            os.makedirs(current_backup_path, exist_ok=True)
            print(f"{self.agent_name}: Created backup directory: {current_backup_path}")

            # 1. Copy essential application data files
            app_data_files_to_copy = {
                "app_settings.json": os.path.join(self.data_root_dir, "app_settings.json"),
                "personal_profiles.json": os.path.join(self.data_root_dir, "personal_profiles.json"),
                "active_sessions.json": os.path.join(self.data_root_dir, "active_sessions.json") # From DocumentTracker
            }

            for filename, source_path in app_data_files_to_copy.items():
                if os.path.exists(source_path):
                    try:
                        shutil.copy2(source_path, os.path.join(current_backup_path, filename))
                        print(f"Copied {filename} to backup.")
                    except Exception as e_file:
                        print(f"Error copying {filename} to backup: {e_file}")
                else:
                    print(f"Skipping {filename}, not found at {source_path}.")

            # 2. Copy document files (trusts, charters, deposits)
            document_types_info = {
                "trusts": {"ext": ".mpea_trust", "path": os.path.join(self.data_root_dir, "trusts")},
                "charters": {"ext": ".mpea_charter", "path": os.path.join(self.data_root_dir, "charters")},
                "deposits": {"ext": ".mpea_deposit", "path": os.path.join(self.data_root_dir, "deposits")}
            }

            for doc_type, info in document_types_info.items():
                source_doc_dir = info["path"]
                backup_doc_type_dir = os.path.join(current_backup_path, doc_type)

                if os.path.exists(source_doc_dir):
                    os.makedirs(backup_doc_type_dir, exist_ok=True)
                    copied_count = 0
                    for item_name in os.listdir(source_doc_dir):
                        if item_name.endswith(info["ext"]):
                            source_item_path = os.path.join(source_doc_dir, item_name)
                            dest_item_path = os.path.join(backup_doc_type_dir, item_name)
                            try:
                                shutil.copy2(source_item_path, dest_item_path)
                                copied_count +=1
                            except Exception as e_doc:
                                print(f"Error copying document {source_item_path} to backup: {e_doc}")
                    print(f"Copied {copied_count} '{doc_type}' documents to backup.")
                else:
                    print(f"Skipping '{doc_type}' documents, directory not found: {source_doc_dir}")

            # Optionally, could also backup codex_vault_sources/uploads if needed, or other specific dirs.

            print(f"{self.agent_name}: Backup successfully completed to {current_backup_path}")
            self.set_status("Idle")
            return current_backup_path
        except Exception as e:
            self.log_error(f"Backup failed: {e}")
            # Clean up partially created backup directory if error occurs during its creation or top-level ops
            if os.path.exists(current_backup_path) and not os.listdir(current_backup_path): # if empty
                try:
                    os.rmdir(current_backup_path)
                except OSError: pass # ignore if not empty due to partial success
            elif os.path.exists(current_backup_path): # if not empty, but failed, user might want to inspect
                print(f"Note: Backup directory {current_backup_path} may contain partial data due to error.")

            return None


class AuditResponse(BaseAgent):
    """
    Behaves as a "Devil's Advocate," interrogating logic and simulating hostile court challenges.
    """
    def __init__(self, app_context=None):
        super().__init__(agent_name="AuditResponse", app_context=app_context)

    def simulate_hostile_challenge(self, document_to_challenge): # document_to_challenge would be a Document object
        self.set_status(f"Simulating hostile challenge for document: {document_to_challenge.name if document_to_challenge else 'N/A'}")
        if not document_to_challenge:
            self.log_error("No document provided for challenge simulation.")
            return None

        # Placeholder: Logic to analyze document clauses against potential legal attacks.
        # This involves deep legal knowledge and understanding of court procedures.
        print(f"{self.agent_name}: Analyzing '{document_to_challenge.name}' for vulnerabilities under simulated hostile challenge. (Placeholder)")
        challenge_report = {
            "document_id": document_to_challenge.id,
            "vulnerabilities_found": 0, # Example: 2
            "points_of_weakness": [], # Example: ["Clause X.Y lacks clear jurisdictional anchor.", "Proof of Z insufficient."]
            "recommended_actions": [],
            "admissibility_score": "N/A" # Example: "High" or "Medium with caveats"
        }
        self.set_status("Idle")
        return challenge_report

class DocumentTracker(BaseAgent): # Renamed from ScrollResumer
    """
    Remembers every document in progress and reopens work without loss.
    """
    def __init__(self, app_context=None):
        super().__init__(agent_name="DocumentTracker (formerly ScrollResumer)", app_context=app_context)
        self.active_sessions_file = os.path.join("data", "active_sessions.json")
        self.active_documents = self._load_active_sessions() # Dict of doc_id: {path, last_state_snapshot}

    def _load_active_sessions(self):
        if os.path.exists(self.active_sessions_file):
            try:
                with open(self.active_sessions_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {self.active_sessions_file}. Starting with empty sessions.")
                return {}
        return {}

    def _save_active_sessions(self):
        try:
            with open(self.active_sessions_file, 'w') as f:
                json.dump(self.active_documents, f, indent=4)
        except Exception as e:
            self.log_error(f"Could not save active sessions: {e}")


    def track_document_open(self, document_id: str, document_path: str, current_state_snapshot: dict):
        self.set_status(f"Tracking document open: {document_id}")
        self.active_documents[document_id] = {
            "path": document_path,
            "last_snapshot": current_state_snapshot, # A dict representation of the document
            "timestamp": datetime.datetime.now().isoformat()
        }
        self._save_active_sessions()
        print(f"{self.agent_name}: Document '{document_id}' at '{document_path}' is now being tracked.")
        self.set_status("Idle")

    def track_document_change(self, document_id: str, updated_state_snapshot: dict):
        if document_id in self.active_documents:
            self.set_status(f"Updating tracked state for document: {document_id}")
            self.active_documents[document_id]["last_snapshot"] = updated_state_snapshot
            self.active_documents[document_id]["timestamp"] = datetime.datetime.now().isoformat()
            self._save_active_sessions()
            print(f"{self.agent_name}: Updated state for tracked document '{document_id}'.")
            self.set_status("Idle")
        else:
            self.log_error(f"Attempted to update untracked document: {document_id}")


    def get_last_session(self, document_id: str):
        self.set_status(f"Retrieving last session for document: {document_id}")
        session_data = self.active_documents.get(document_id)
        if session_data:
            print(f"{self.agent_name}: Last session data found for '{document_id}'.")
        else:
            print(f"{self.agent_name}: No active session found for '{document_id}'.")
        self.set_status("Idle")
        return session_data

    def untrack_document(self, document_id: str):
        if document_id in self.active_documents:
            self.set_status(f"Stopping tracking for document: {document_id}")
            del self.active_documents[document_id]
            self._save_active_sessions()
            print(f"{self.agent_name}: Document '{document_id}' is no longer tracked.")
            self.set_status("Idle")


# Example of how these might be instantiated and managed by the main app (conceptual)
# class ApplicationContext:
#     def __init__(self):
#         self.settings = SettingsView().settings # Assuming settings are loaded
#         self.documents = {} # Holds loaded Document objects
#         # ... other shared resources

# if __name__ == "__main__":
#     import datetime # Required for AutoBackup and DocumentTracker examples
#     app_ctx = ApplicationContext() # Conceptual application context

#     master_ai = PostalEquityAppAI(app_context=app_ctx)
#     conformer = ClauseConformer(app_context=app_ctx)
#     sentinel = CodexSentinel(app_context=app_ctx)
#     proof_gen = VeritasProof(app_context=app_ctx)
#     drift_monitor = DriftGuard(app_context=app_ctx)
#     backup_agent = AutoBackup(app_context=app_ctx)
#     audit_sim = AuditResponse(app_context=app_ctx)
#     doc_tracker = DocumentTracker(app_context=app_ctx)

#     print("\n--- Agent Statuses ---")
#     for agent in [master_ai, conformer, sentinel, proof_gen, drift_monitor, backup_agent, audit_sim, doc_tracker]:
#         print(agent.get_status())

#     print("\n--- Example Operations ---")
#     master_ai.interpret_command("Generate Trust for Rene Michaud")
#     # backup_agent.perform_backup() # This would create a placeholder file in data/backups

#     # Simulate opening and tracking a document
#     # dummy_trust_data = {"id": "trust123", "name": "Test Trust", "clauses": ["Clause A"]} # Simplified
#     # doc_tracker.track_document_open("trust123", "data/trusts/test_trust.mpea_trust", dummy_trust_data)
#     # last_session = doc_tracker.get_last_session("trust123")
#     # if last_session:
#     #     print(f"Last session snapshot: {last_session['last_snapshot']}")

#     # To clean up test files created by DocumentTracker or AutoBackup:
#     # if os.path.exists(doc_tracker.active_sessions_file):
#     #     os.remove(doc_tracker.active_sessions_file)
#     # backup_dir = os.path.join("data", "backups")
#     # if os.path.exists(backup_dir):
#     #     for f in os.listdir(backup_dir):
#     #         os.remove(os.path.join(backup_dir, f))
#     #     # os.rmdir(backup_dir) # if empty
#     pass
