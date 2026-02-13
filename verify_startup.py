
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

try:
    print("Importing modules...")
    from acc.app import ACCApp
    from acc.widgets.grid import SessionGrid, SessionCard
    from acc.widgets.session_table import SessionTable
    from acc.discovery import Session, SessionStatus
    
    print("Instantiating ACCApp...")
    app = ACCApp()
    
    print("Instantiating SessionTable...")
    table = SessionTable(id="test-table")
    
    print("Instantiating SessionGrid...")
    grid = SessionGrid(id="test-grid")
    
    print("Instantiating SessionCard...")
    dummy_session = Session(
        pane_id="test:0.0", pane_pid=123, session_name="test",
        window_index=0, pane_index=0, status=SessionStatus.IDLE
    )
    card = SessionCard(dummy_session)
    
    print("Simulating Compose...")
    # diverse compose logic
    layout = app.compose()
    # It's a generator
    for widget in layout:
        pass
        
    print("Verification PASSED: No startup crashes detected.")

except Exception as e:
    print(f"Verification FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
