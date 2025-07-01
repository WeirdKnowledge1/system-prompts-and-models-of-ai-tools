# Michaud Postal Equity App (MPEA)

This application is being developed to assist with the creation and management of legal and postal documents according to the specifications provided.

## Project Goal

To build a comprehensive, autonomous, and lawful interface for document creation, postal dominion tracking, jurisdictional conversion, clause harmonization, and AI-driven execution within full equity authority, as per the detailed system specifications.

## Current Phase: Phase 1 - Core Document Structure and Basic UI

### Key Objectives for Phase 1:
1.  **Project Setup & Initial UI Shell:**
    *   Python with PyQt6 for the GUI.
    *   Main application window with tabbed interface for Trust, Charter, Deposit, Settings, Ledgers.
2.  **Define Core Document Models:**
    *   Initial Python classes for Trust, Charter, Deposit documents.
3.  **Basic Document Builder UI (Trust, Charter, Deposit):**
    *   Simple UI views for manual data entry.
    *   Basic Save/Load functionality (e.g., JSON/XML).
4.  **Initial Settings Panel:**
    *   Basic UI for the first few System Preference toggles (UI only).
5.  **Stub AI Agent Infrastructure:**
    *   Placeholder Python classes for core AI agents.

## Setup and Installation (Tentative)

1.  Ensure Python 3.x is installed.
2.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the application:
    ```bash
    python main.py
    ```

## Project Structure

```
michaud_postal_equity_app/
|-- main.py                 # Main application entry point
|-- app/
|   |-- __init__.py
|   |-- ui/
|   |   |-- __init__.py
|   |   |-- main_window.py      # Main application window
|   |   |-- trust_view.py       # UI for Michaud Family Trust
|   |   |-- charter_view.py     # UI for Family Postal Charter
|   |   |-- deposit_view.py     # UI for Special Deposit Document
|   |   |-- settings_view.py    # UI for System Preferences
|   |   |-- ledger_view.py      # UI for Ledgers
|   |   |-- widgets/            # Custom UI widgets
|   |       |-- __init__.py
|   |-- core/
|   |   |-- __init__.py
|   |   |-- document_models.py  # Data models for Trust, Charter, Deposit
|   |   |-- clause_model.py     # Data model for Clauses
|   |   |-- agents.py           # AI agent classes
|   |-- utils/
|   |   |-- __init__.py
|   |   |-- constants.py        # Application constants
|-- data/                     # For storing saved documents (Codex Vault)
|   |-- trusts/
|   |-- charters/
|   |-- deposits/
|   |-- backups/
|   |-- codex_vault_sources/  # For user uploaded source files
|   |   |-- uploads/
|   |-- zip_modules/          # For ZIP module upgrades
|-- assets/                   # For icons, images etc.
|-- requirements.txt          # Python dependencies
|-- README.md
|-- AGENTS.md                 # (If provided)
```

## Contributing

Details to be added as the project progresses.

## License

To be determined.
