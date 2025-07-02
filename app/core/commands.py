from abc import ABC, abstractmethod
import datetime # For EditClauseCommand if it handles timestamps
from app.core.clause_model import Clause # For type hinting

class Command(ABC):
    """
    Abstract base class for all commands in the Command pattern.
    Commands encapsulate an action and its inverse (undo).
    """
    @abstractmethod
    def execute(self):
        """Executes the command, performing the action."""
        pass

    @abstractmethod
    def undo(self):
        """Reverts the command, undoing the action performed by execute()."""
        pass

    def __str__(self):
        return self.__class__.__name__

# --- Concrete Command Implementations for Clause Operations ---

class AddClauseCommand(Command):
    """Command to add a clause to a document's clause list."""
    def __init__(self, clauses_list: list, clause_obj: Clause, insert_index: int = -1):
        self.clauses_list = clauses_list
        self.clause_obj = clause_obj
        self.insert_index = insert_index if 0 <= insert_index <= len(self.clauses_list) else len(self.clauses_list)
        self._executed_successfully = False

    def execute(self):
        actual_insert_index = min(self.insert_index, len(self.clauses_list))
        self.clauses_list.insert(actual_insert_index, self.clause_obj)
        self.insert_index = actual_insert_index # Store actual index of insertion for undo
        self._executed_successfully = True
        # print(f"Executed Add: {self.clause_obj.id} at {self.insert_index}")

    def undo(self):
        if self._executed_successfully:
            try:
                self.clauses_list.remove(self.clause_obj)
                # print(f"Undid Add: {self.clause_obj.id}")
            except ValueError:
                print(f"Warning: Undo AddClause failed to find {self.clause_obj.id} for removal.")
        # else:
            # print(f"Warning: Undo AddClause called but not executed or clause already removed: {self.clause_obj.id}")

    def __str__(self):
        return f"AddClause(id='{self.clause_obj.id[:8]}', idx={self.insert_index})"


class RemoveClauseCommand(Command):
    """Command to remove a clause from a document's clause list."""
    def __init__(self, clauses_list: list, clause_obj: Clause, original_index: int):
        self.clauses_list = clauses_list
        self.clause_obj = clause_obj
        self.original_index = original_index
        self._executed_successfully = False

    def execute(self):
        # print(f"Executing Remove: {self.clause_obj.id} (expected at {self.original_index})")
        try:
            # It's crucial that original_index is correct at the time of command creation.
            # If the list could have been modified by other means (which command pattern tries to avoid),
            # then removing by object identity is safer, but original_index is vital for undo.
            if 0 <= self.original_index < len(self.clauses_list) and \
               self.clauses_list[self.original_index] == self.clause_obj:
                self.clauses_list.pop(self.original_index)
                self._executed_successfully = True
            elif self.clause_obj in self.clauses_list: # Fallback: object is in list but not at original_index
                print(f"Warning: Clause {self.clause_obj.id} not at original_index {self.original_index}, removing by identity.")
                self.original_index = self.clauses_list.index(self.clause_obj) # Update index for undo
                self.clauses_list.remove(self.clause_obj)
                self._executed_successfully = True
            else:
                print(f"Warning: RemoveClause execute failed, clause {self.clause_obj.id} not found.")
                self._executed_successfully = False
        except (ValueError, IndexError) as e:
            print(f"Error executing RemoveClause for {self.clause_obj.id}: {e}")
            self._executed_successfully = False

    def undo(self):
        if self._executed_successfully:
            # print(f"Undoing Remove: Re-inserting {self.clause_obj.id} at {self.original_index}")
            idx_to_insert = min(self.original_index, len(self.clauses_list))
            self.clauses_list.insert(idx_to_insert, self.clause_obj)
        # else:
            # print(f"Warning: Undo RemoveClause called but not executed successfully: {self.clause_obj.id}")

    def __str__(self):
        return f"RemoveClause(id='{self.clause_obj.id[:8]}', idx={self.original_index})"


class EditClauseCommand(Command):
    """Command to edit attributes of a clause. Assumes clause_obj is a live reference."""
    def __init__(self, clause_obj: Clause, old_attributes: dict, new_attributes: dict):
        self.clause_obj = clause_obj
        self.old_attributes = old_attributes.copy()
        self.new_attributes = new_attributes.copy()

        # Capture initial version and last_modified_date if not explicitly passed in old_attributes
        # These are crucial for correct undo state.
        if 'version' not in self.old_attributes and hasattr(self.clause_obj, 'version'):
            self.old_attributes['version'] = self.clause_obj.version
        if 'last_modified_date' not in self.old_attributes and hasattr(self.clause_obj, 'last_modified_date'):
            self.old_attributes['last_modified_date'] = self.clause_obj.last_modified_date

    def _apply_attributes(self, target_clause: Clause, attributes_to_apply: dict):
        for attr_name, value in attributes_to_apply.items():
            setattr(target_clause, attr_name, value)

        # If this application of attributes represents the 'execute' phase (applying new_attributes),
        # then we should also handle the version and modification date updates.
        # The EditClauseDialog should ideally provide the new_attributes already reflecting
        # any changes it made, including to version and last_modified_date.
        # If not, this command needs to be smarter or make assumptions.
        # For now, assume version and last_modified_date are part of new_attributes if they changed.
        # If they are NOT part of new_attributes, it means the dialog didn't intend for them to change
        # beyond what the clause model might do internally if its setters are called.
        # However, for robustness in undo/redo, explicitly setting them is better.

        # If we're applying NEW attributes (execute):
        if attributes_to_apply == self.new_attributes:
            if hasattr(target_clause, 'version'): # Ensure attribute exists
                 target_clause.version += 1
            if hasattr(target_clause, 'last_modified_date'): # Ensure attribute exists
                 target_clause.last_modified_date = datetime.datetime.now().isoformat()


    def execute(self):
        # print(f"Executing Edit: {self.clause_obj.id} with {self.new_attributes}")
        self._apply_attributes(self.clause_obj, self.new_attributes)

    def undo(self):
        # print(f"Undoing Edit: {self.clause_obj.id} with {self.old_attributes}")
        self._apply_attributes(self.clause_obj, self.old_attributes)
        # When undoing, the old_attributes should contain the correct historical
        # version and last_modified_date, which _apply_attributes will set.

    def __str__(self):
        changed_attrs = ", ".join(self.new_attributes.keys())
        return f"EditClause(id='{self.clause_obj.id[:8]}', attrs=[{changed_attrs}])"


class MoveClauseCommand(Command):
    """Command to move a clause within a document's clause list."""
    def __init__(self, clauses_list: list, clause_obj_to_move: Clause, from_index: int, to_index_visual: int):
        self.clauses_list = clauses_list
        self.clause_obj_to_move = clause_obj_to_move
        self.from_index = from_index # Original index before move
        self.to_index_visual = to_index_visual # Target index as user perceives it (e.g., if dragging to 5th slot)
        self._actual_to_index_on_execute = -1 # Internal: actual insertion index after removal

    def execute(self):
        # print(f"Executing Move: {self.clause_obj_to_move.id} from {self.from_index} to visual {self.to_index_visual}")
        try:
            # Ensure the object is at from_index or find it if list was manipulated (should not happen with commands)
            if not (0 <= self.from_index < len(self.clauses_list) and \
                    self.clauses_list[self.from_index] == self.clause_obj_to_move):
                try: # Fallback: find object if from_index is stale
                    self.from_index = self.clauses_list.index(self.clause_obj_to_move)
                except ValueError:
                    print(f"Error executing MoveClause: Clause {self.clause_obj_to_move.id} not found.")
                    return

            clause = self.clauses_list.pop(self.from_index)

            # Calculate actual insertion index
            # If item was removed from an index *before* its visual target, the target index shifts down by 1.
            self._actual_to_index_on_execute = self.to_index_visual
            if self.from_index < self.to_index_visual:
                self._actual_to_index_on_execute -= 1

            # Clamp index to be within valid bounds of the (now shorter) list
            self._actual_to_index_on_execute = max(0, min(len(self.clauses_list), self._actual_to_index_on_execute))

            self.clauses_list.insert(self._actual_to_index_on_execute, clause)
            # print(f"  Moved to actual index: {self._actual_to_index_on_execute}")

        except IndexError as e:
            print(f"Error executing MoveClause (IndexError): {e}")
        except Exception as e_gen:
            print(f"Unexpected error executing MoveClause: {e_gen}")

    def undo(self):
        # print(f"Undoing Move: {self.clause_obj_to_move.id} back to {self.from_index}")
        try:
            # Remove from its current executed position.
            # It's safer to remove by object identity than relying on self._actual_to_index_on_execute
            # if other commands could have run and shifted things (though unlikely with simple undo/redo).
            self.clauses_list.remove(self.clause_obj_to_move)

            # Re-insert at the original from_index (clamped)
            actual_from_index = max(0, min(len(self.clauses_list), self.from_index))
            self.clauses_list.insert(actual_from_index, self.clause_obj_to_move)
        except ValueError:
            print(f"Error undoing MoveClause: Clause {self.clause_obj_to_move.id} not found.")
        except Exception as e_gen:
            print(f"Unexpected error undoing MoveClause: {e_gen}")

    def __str__(self):
        return f"MoveClause(id='{self.clause_obj_to_move.id[:8]}', from={self.from_index}, to_visual={self.to_index_visual})"


if __name__ == '__main__':
    # Mock Clause for testing commands
    class MockClauseForCmd(Clause): # Inherit from real Clause for attributes
        def __init__(self, text, clause_id=None, **kwargs):
            super().__init__(text=text, clause_id=clause_id, **kwargs)
        def __repr__(self):
            return f"MockClause(id='{self.id[:8]}', text='{self.text[:10]}...')"

    print("Testing Concrete Command Classes...")
    clauses = []

    # Test AddClauseCommand
    print("\n--- Testing AddClauseCommand ---")
    clause1_to_add = MockClauseForCmd("First test clause", clause_id="C1")
    add_cmd1 = AddClauseCommand(clauses, clause1_to_add)
    print(f"Before add: {clauses}")
    add_cmd1.execute()
    print(f"After add: {clauses}")
    assert len(clauses) == 1 and clauses[0] == clause1_to_add
    add_cmd1.undo()
    print(f"After undo: {clauses}")
    assert len(clauses) == 0

    clause2_to_add = MockClauseForCmd("Second test clause", clause_id="C2")
    add_cmd2 = AddClauseCommand(clauses, clause2_to_add, insert_index=0) # Insert at beginning
    add_cmd2.execute() # clauses = [C2]
    clause3_to_add = MockClauseForCmd("Third test clause", clause_id="C3")
    add_cmd3 = AddClauseCommand(clauses, clause3_to_add, insert_index=1) # Insert in middle
    add_cmd3.execute() # clauses = [C2, C3]
    print(f"After multiple adds: {clauses}")
    assert len(clauses) == 2 and clauses[0] == clause2_to_add and clauses[1] == clause3_to_add
    add_cmd3.undo() # clauses = [C2]
    print(f"After undo add_cmd3: {clauses}")
    assert len(clauses) == 1 and clauses[0] == clause2_to_add
    add_cmd2.undo() # clauses = []
    print(f"After undo add_cmd2: {clauses}")
    assert len(clauses) == 0

    # Test RemoveClauseCommand
    print("\n--- Testing RemoveClauseCommand ---")
    c_rem1 = MockClauseForCmd("To Remove 1", clause_id="CR1")
    c_rem2 = MockClauseForCmd("To Keep 1", clause_id="CK1")
    clauses = [c_rem1, c_rem2]
    print(f"Before remove: {clauses}")
    remove_cmd1 = RemoveClauseCommand(clauses, c_rem1, original_index=0)
    remove_cmd1.execute()
    print(f"After remove c_rem1: {clauses}")
    assert len(clauses) == 1 and clauses[0] == c_rem2
    remove_cmd1.undo()
    print(f"After undo remove_cmd1: {clauses}")
    assert len(clauses) == 2 and clauses[0] == c_rem1

    # Test EditClauseCommand
    print("\n--- Testing EditClauseCommand ---")
    clause_to_edit = MockClauseForCmd("Original Text", clause_id="CE1", jurisdiction="Lex Aequies", level=1)
    print(f"Before edit: {clause_to_edit.to_dict()}")
    old_attrs = {"text": "Original Text", "jurisdiction": "Lex Aequies", "level": 1,
                 "version": clause_to_edit.version, "last_modified_date": clause_to_edit.last_modified_date}
    new_attrs = {"text": "Updated Text!", "jurisdiction": "Lex Postalis", "level": 2}
    edit_cmd = EditClauseCommand(clause_to_edit, old_attrs, new_attrs)

    # Simulate what EditClauseDialog might do: it updates the clause, then we create command
    # For testing command, we assume clause_obj has new state, old_state is captured.
    # Actually, EditClauseCommand's execute should apply the new state.
    # So, clause_to_edit starts with old state.

    edit_cmd.execute()
    print(f"After edit execute: {clause_to_edit.to_dict()}")
    assert clause_to_edit.text == "Updated Text!" and clause_to_edit.jurisdiction == "Lex Postalis" and clause_to_edit.level == 2

    edit_cmd.undo()
    print(f"After edit undo: {clause_to_edit.to_dict()}")
    assert clause_to_edit.text == "Original Text" and clause_to_edit.jurisdiction == "Lex Aequies" and clause_to_edit.level == 1

    # Test MoveClauseCommand
    print("\n--- Testing MoveClauseCommand ---")
    mc1 = MockClauseForCmd("MoveClause1", clause_id="MC1")
    mc2 = MockClauseForCmd("MoveClause2", clause_id="MC2")
    mc3 = MockClauseForCmd("MoveClause3", clause_id="MC3")
    clauses = [mc1, mc2, mc3]
    print(f"Before move: {clauses}")
    # Move mc1 (idx 0) to visual index 2 (i.e., after mc3 if it were there)
    move_cmd1 = MoveClauseCommand(clauses, mc1, from_index=0, to_index_visual=2)
    move_cmd1.execute() # Expected: [mc2, mc3, mc1]
    print(f"After move mc1 from 0 to 2 (visual): {clauses}")
    assert clauses == [mc2, mc3, mc1]
    move_cmd1.undo() # Expected: [mc1, mc2, mc3]
    print(f"After undo move mc1: {clauses}")
    assert clauses == [mc1, mc2, mc3]

    # Move mc3 (idx 2) to visual index 0
    move_cmd2 = MoveClauseCommand(clauses, mc3, from_index=2, to_index_visual=0)
    move_cmd2.execute() # Expected: [mc3, mc1, mc2]
    print(f"After move mc3 from 2 to 0 (visual): {clauses}")
    assert clauses == [mc3, mc1, mc2]
    move_cmd2.undo() # Expected: [mc1, mc2, mc3]
    print(f"After undo move mc3: {clauses}")
    assert clauses == [mc1, mc2, mc3]

    # Move mc2 (idx 1) to visual index 1 (no change)
    move_cmd3 = MoveClauseCommand(clauses, mc2, from_index=1, to_index_visual=1)
    move_cmd3.execute()
    print(f"After move mc2 from 1 to 1 (visual): {clauses}")
    assert clauses == [mc1, mc2, mc3]
    move_cmd3.undo()
    print(f"After undo move mc2: {clauses}")
    assert clauses == [mc1, mc2, mc3]

    print("\nAll concrete command tests finished.")
