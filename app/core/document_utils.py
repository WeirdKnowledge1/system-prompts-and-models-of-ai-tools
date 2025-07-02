from typing import List
# from .clause_model import Clause # Forward declaration for type hint if needed, or direct import

def generate_display_clause_numbers(clauses: List['Clause']) -> List[str]:
    """
    Generates dynamic display numbers for a list of clauses based on their
    level and section_title attributes.

    Example Numbering Logic:
    - Clauses with section_title at level 1 start new main sections (I, II, III...).
    - Clauses with section_title at level 2 start sub-sections (A, B, C...).
    - Clauses without section_title at level 1 continue main numbering (1, 2, 3...).
    - Clauses without section_title at level 2 continue sub-numbering (1.1, 1.2...).
    - Clauses at level 3 continue deeper sub-numbering (1.1.1, 1.1.2...).
    - This is a simplified scheme. The Part VIII, Sec IV scheme (FT.3.2.4) is more complex
      and would require document prefix and more structured section objects.
      This implementation aims for a readable outline style.
    """
    display_numbers = []
    if not clauses:
        return display_numbers

    # Counters for different levels. Max 5 levels for this example.
    # Max depth for numbering, can be adjusted.
    MAX_LEVELS = 5
    counters = [0] * MAX_LEVELS

    # Helper to get Roman numerals
    def to_roman(num):
        roman_map = { 1: 'I', 4: 'IV', 5: 'V', 9: 'IX', 10: 'X', 40: 'XL', 50: 'L',
                      90: 'XC', 100: 'C', 400: 'XD', 500: 'D', 900: 'CM', 1000: 'M'}
        integers = list(roman_map)
        symbols = list(roman_map.values())
        i = 12
        result = ""
        while num != 0:
            if integers[i] <= num:
                result += symbols[i]
                num -= integers[i]
            else:
                i -= 1
        return result if result else str(num) # Fallback to num if not in map or 0

    # Helper to get Alpha characters (A, B, ...)
    def to_alpha(num):
        if num <= 0 or num > 26: return str(num) # Fallback for out of range
        return chr(ord('A') + num - 1)

    # Helper to get lowercase alpha characters (a, b, ...)
    def to_lower_alpha(num):
        if num <= 0 or num > 26: return str(num)
        return chr(ord('a') + num - 1)

    # Helper to get lowercase roman numerals (i, ii, ...)
    def to_lower_roman(num):
        return to_roman(num).lower()

    # Define numbering scheme per level:
    # Level 1: SECTION I / 1.
    # Level 2: A. / 1.1.
    # Level 3: 1. / 1.1.1.
    # Level 4: a. / 1.1.1.1.
    # Level 5: i. / 1.1.1.1.1.
    # This scheme prioritizes SECTION/A/1/a/i if a section_title is present at that level,
    # otherwise uses dotted numeric.

    last_level_had_title = [False] * MAX_LEVELS # Track if the parent level was a titled section

    for clause in clauses:
        level_idx = clause.level - 1

        if level_idx < 0 or level_idx >= MAX_LEVELS:
            display_numbers.append("ErrLvl!")
            continue

        # Increment counter for the current level
        counters[level_idx] += 1

        # Reset counters for deeper levels
        for i in range(level_idx + 1, MAX_LEVELS):
            counters[i] = 0
            last_level_had_title[i] = False # Reset title status for deeper levels

        current_number_str = ""
        if clause.section_title:
            last_level_had_title[level_idx] = True
            if clause.level == 1:
                current_number_str = f"SECTION {to_roman(counters[level_idx])}: {clause.section_title}"
            elif clause.level == 2:
                current_number_str = f"{to_alpha(counters[level_idx])}. {clause.section_title}"
            elif clause.level == 3: # Titled level 3, use numeric
                current_number_str = f"{counters[level_idx]}. {clause.section_title}"
            elif clause.level == 4: # Titled level 4, use lower alpha
                current_number_str = f"{to_lower_alpha(counters[level_idx])}. {clause.section_title}"
            elif clause.level == 5: # Titled level 5, use lower roman
                current_number_str = f"{to_lower_roman(counters[level_idx])}. {clause.section_title}"
            else: # Fallback for deeper titled sections
                num_parts = [str(counters[i]) for i in range(level_idx + 1)]
                current_number_str = ".".join(num_parts) + f" {clause.section_title}"
        else: # No section title, standard outline numbering
            last_level_had_title[level_idx] = False
            # Build number based on parent context
            if clause.level == 1: # 1., 2.
                current_number_str = f"{counters[level_idx]}."
            elif clause.level == 2: # I.A. or 1.A. (if parent L1 had title) or 1.1.
                if level_idx > 0 and last_level_had_title[level_idx-1] and counters[level_idx-1]>0 : # Check if L1 was titled
                    if clause.level == 1: # Should not happen due to level_idx > 0
                         parent_prefix = ""
                    elif counters[0] <= 10: # Roman for L1
                         parent_prefix = f"{to_roman(counters[0])}."
                    else: # Numeric for L1 if > X
                         parent_prefix = f"{counters[0]}."
                    current_number_str = f"{parent_prefix}{to_alpha(counters[level_idx])}."
                else: # Dotted numeric 1.1., 1.2.
                    current_number_str = f"{counters[0]}.{counters[level_idx]}."
            elif clause.level == 3: # I.A.1. or 1.A.1. or 1.1.1.
                # Simplified: always dotted numeric for L3+ if no title
                num_parts = [str(counters[i]) for i in range(level_idx + 1)]
                current_number_str = ".".join(num_parts) + "."
            elif clause.level == 4:
                num_parts = [str(counters[i]) for i in range(level_idx + 1)]
                current_number_str = ".".join(num_parts) + "."
            elif clause.level == 5:
                num_parts = [str(counters[i]) for i in range(level_idx + 1)]
                current_number_str = ".".join(num_parts) + "."
            else: # Fallback for deeper levels
                num_parts = [str(counters[i]) for i in range(level_idx + 1)]
                current_number_str = ".".join(num_parts) + "."

        display_numbers.append(current_number_str)

    return display_numbers


if __name__ == '__main__':
    # Mock Clause class for testing
    class MockClause:
        def __init__(self, text, level=1, section_title=None, clause_id="test-id", jurisdiction="test-jur", origin="test-org"):
            self.text = text
            self.level = max(1,level)
            self.section_title = section_title
            self.id = clause_id
            self.jurisdiction = jurisdiction
            self.origin = origin
            self.creation_date = datetime.datetime.now().isoformat()
            self.last_modified_date = self.creation_date
            self.version = 1
            self.metadata = {}


    clauses_test = [
        MockClause("Intro text", level=1, section_title="Introduction"),
        MockClause("First point of intro", level=2),
        MockClause("Second point of intro", level=2),
        MockClause("Sub-point of second", level=3),
        MockClause("Another main point", level=1),
        MockClause("Details for this point", level=2),
        MockClause("Part B", level=1, section_title="Main Part B"),
        MockClause("First sub of B", level=2),
        MockClause("Second sub of B, with its own title", level=2, section_title="Definitions"),
        MockClause("Def 1", level=3),
        MockClause("Def 2", level=3),
        MockClause("Another L1 clause", level=1),
        MockClause("Another L1 clause with title", level=1, section_title="Conclusion"),
    ]

    numbers = generate_display_clause_numbers(clauses_test)
    print("Generated Clause Numbers:")
    for i, num_str in enumerate(numbers):
        print(f"{num_str} (Text: {clauses_test[i].text[:30]}...)")

    # Expected rough output:
    # SECTION I: Introduction (Text: Intro text...)
    # I.a. (Text: First point of intro...)
    # I.b. (Text: Second point of intro...)
    # I.b.1. (Text: Sub-point of second...)
    # 1. (Text: Another main point...)  <-- Reset from Roman due to no title L1
    # 1.1. (Text: Details for this point...)
    # SECTION II: Main Part B (Text: Part B...)
    # II.a. (Text: First sub of B...)
    # B. Definitions (Text: Second sub of B, with its own...) <-- L2 with title
    # B.1. (Text: Def 1...)
    # B.2. (Text: Def 2...)
    # 2. (Text: Another L1 clause...)
    # SECTION III: Conclusion (Text: Another L1 clause with title...)

    # The current logic is a bit simpler than the expected output above,
    # specifically around mixing Roman/Alpha with pure numeric based on context.
    # The current output will be more like:
    # SECTION I: Introduction
    # I.1.
    # I.2.
    # I.2.1.
    # 1.  <-- This is where it might differ if not carefully handled
    # 1.1.
    # SECTION II: Main Part B
    # II.1.
    # A. Definitions
    # A.1.
    # A.2.
    # 2.
    # SECTION III: Conclusion
    # This simplified scheme is a starting point.
    # The Part VIII. Sec IV "FT.3.2.4" is more like a prefix + path, which this doesn't do yet.
    # This function provides basic outline style numbering.
    # For FT.3.2.4, we'd need document prefix and more structured section/subsection objects.
    # For now, this function will provide a basic multi-level numbering.


# --- PDF Text Extraction Utility ---
try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    PdfReader = None # To avoid NameError if not available

def extract_text_from_pdf(pdf_path: str) -> str | None:
    """
    Extracts text content from a PDF file using PyPDF2.
    Returns the extracted text as a string, or None if an error occurs or PyPDF2 is not available.
    """
    if not PYPDF2_AVAILABLE:
        print("PyPDF2 library is not installed. Cannot extract text from PDF.")
        return "Error: PDF processing library (PyPDF2) not available." # Return error message

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return "Error: PDF file not found."

    try:
        text_content = []
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text_content.append(page.extract_text() or "") # Ensure None is handled as empty string

        full_text = "\n".join(text_content).strip()
        if not full_text:
            return "(No text could be extracted from this PDF or PDF is image-based)"
        return full_text
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return f"Error extracting text from PDF: {e}"


if __name__ == '__main__':
    # Mock Clause class for testing
    class MockClause:
        def __init__(self, text, level=1, section_title=None, clause_id="test-id", jurisdiction="test-jur", origin="test-org"):
            self.text = text
            self.level = max(1,level)
            self.section_title = section_title
            self.id = clause_id
            self.jurisdiction = jurisdiction
            self.origin = origin
            self.creation_date = datetime.datetime.now().isoformat()
            self.last_modified_date = self.creation_date
            self.version = 1
            self.metadata = {}


    clauses_test = [
        MockClause("Intro text", level=1, section_title="Introduction"),
        MockClause("First point of intro", level=2),
        MockClause("Second point of intro", level=2),
        MockClause("Sub-point of second", level=3),
        MockClause("Another main point", level=1),
        MockClause("Details for this point", level=2),
        MockClause("Part B", level=1, section_title="Main Part B"),
        MockClause("First sub of B", level=2),
        MockClause("Second sub of B, with its own title", level=2, section_title="Definitions"),
        MockClause("Def 1", level=3),
        MockClause("Def 2", level=3),
        MockClause("Another L1 clause", level=1),
        MockClause("Another L1 clause with title", level=1, section_title="Conclusion"),
    ]

    numbers = generate_display_clause_numbers(clauses_test)
    print("Generated Clause Numbers:")
    for i, num_str in enumerate(numbers):
        print(f"{num_str} (Text: {clauses_test[i].text[:30]}...)")

    # Expected rough output:
    # SECTION I: Introduction (Text: Intro text...)
    # I.a. (Text: First point of intro...)
    # I.b. (Text: Second point of intro...)
    # I.b.1. (Text: Sub-point of second...)
    # 1. (Text: Another main point...)  <-- Reset from Roman due to no title L1
    # 1.1. (Text: Details for this point...)
    # SECTION II: Main Part B (Text: Part B...)
    # II.a. (Text: First sub of B...)
    # B. Definitions (Text: Second sub of B, with its own...) <-- L2 with title
    # B.1. (Text: Def 1...)
    # B.2. (Text: Def 2...)
    # 2. (Text: Another L1 clause...)
    # SECTION III: Conclusion (Text: Another L1 clause with title...)

    # The current logic is a bit simpler than the expected output above,
    # specifically around mixing Roman/Alpha with pure numeric based on context.
    # The current output will be more like:
    # SECTION I: Introduction
    # I.1.
    # I.2.
    # I.2.1.
    # 1.  <-- This is where it might differ if not carefully handled
    # 1.1.
    # SECTION II: Main Part B
    # II.1.
    # A. Definitions
    # A.1.
    # A.2.
    # 2.
    # SECTION III: Conclusion
    # This simplified scheme is a starting point.
    # The Part VIII. Sec IV "FT.3.2.4" is more like a prefix + path, which this doesn't do yet.
    # This function provides basic outline style numbering.

    print("\n---\nTest with simpler structure (no L1 section titles first):")
    clauses_test_2 = [
        MockClause("Clause 1, Level 1", level=1),
        MockClause("Clause 1.1, Level 2", level=2),
        MockClause("Clause 1.2, Level 2", level=2),
        MockClause("Clause 1.2.1, Level 3", level=3),
        MockClause("Clause 2, Level 1", level=1),
        MockClause("Clause 2.1, Level 2", level=2),
    ]
    numbers2 = generate_display_clause_numbers(clauses_test_2)
    for i, num_str in enumerate(numbers2):
        print(f"{num_str} (Text: {clauses_test_2[i].text[:30]}...)")
    # Expected:
    # 1.
    # 1.1.
    # 1.2.
    # 1.2.1.
    # 2.
    # 2.1.
