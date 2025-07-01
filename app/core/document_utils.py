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
    # counters[0] is for level 1, counters[1] for level 2, etc.
    counters = [0] * 5

    # Roman numerals for top-level sections if they have titles
    roman_map = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
                 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"} # Extend as needed

    current_level_1_is_roman = False

    for clause in clauses:
        level_idx = clause.level - 1 # 0-indexed

        if level_idx < 0 or level_idx >= len(counters):
            display_numbers.append("ErrLvl!") # Error for invalid level
            continue

        if clause.section_title:
            if clause.level == 1:
                counters[level_idx] += 1
                # Reset deeper levels
                for i in range(level_idx + 1, len(counters)):
                    counters[i] = 0
                current_number_str = roman_map.get(counters[level_idx], str(counters[level_idx]))
                display_numbers.append(f"SECTION {current_number_str}: {clause.section_title}")
                current_level_1_is_roman = True # Subsequent level 2s will be A, B if under Roman
            elif clause.level == 2: # Sub-section with title (e.g., A. Title)
                counters[level_idx] += 1
                for i in range(level_idx + 1, len(counters)):
                    counters[i] = 0
                # Use A, B, C for level 2 if under a Roman numeral section, or if it's the first type of L2
                # This logic can be refined. For now, always A, B, C for titled L2.
                section_char = chr(ord('A') + counters[level_idx] - 1)
                parent_num_parts = [str(counters[i]) for i in range(level_idx) if counters[i] > 0]
                if current_level_1_is_roman and level_idx > 0: # If parent was Roman, don't prepend its number
                     parent_prefix = ""
                else:
                     parent_prefix = ".".join(parent_num_parts) + "." if parent_num_parts else ""

                # display_numbers.append(f"{parent_prefix}{section_char}. {clause.section_title}")
                # Simplified for now: just "A. Section Title"
                display_numbers.append(f"{section_char}. {clause.section_title}")


            else: # Section titles at deeper levels just get standard numbering
                counters[level_idx] += 1
                for i in range(level_idx + 1, len(counters)):
                    counters[i] = 0
                num_parts = [str(counters[i]) for i in range(level_idx + 1) if counters[i] > 0 or i <= level_idx]
                display_numbers.append(".".join(num_parts) + f" {clause.section_title}")

        else: # No section title, just a numbered clause
            counters[level_idx] += 1
            # Reset deeper levels only if this is not the deepest level being incremented
            # e.g. if we go from 1.1 to 1.2, 1.1.x should reset. If we go from 1.1 to 2.1, 1.x.x should reset.
            # This is implicitly handled if a higher level section_title resets them.
            # If no section titles, this simple counter logic works per level.
            for i in range(level_idx + 1, len(counters)):
                 counters[i] = 0

            num_parts = []
            if current_level_1_is_roman and clause.level > 1: # If under a Roman section
                num_parts.append(roman_map.get(counters[0], str(counters[0])))
                if clause.level == 2: # A, B, C for level 2 items under Roman
                    num_parts.append(chr(ord('a') + counters[1] -1)) # a,b,c
                elif clause.level > 2: # 1,2,3 for deeper levels
                    for i in range(2, level_idx + 1):
                         num_parts.append(str(counters[i]))
            else: # Standard numeric hierarchy
                for i in range(level_idx + 1):
                    num_parts.append(str(counters[i]))

            display_numbers.append(".".join(num_parts) + ".")
            if clause.level == 1 : current_level_1_is_roman = False # Reset if we start a new numeric L1

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
