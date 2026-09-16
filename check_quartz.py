try:
    import Quartz
    import sys
    print("Quartz imported successfully")
    
    # Try to create an event (won't post it, just create)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (100, 100), 0)
    if e:
        print("CGEventCreateMouseEvent worked")
    else:
        print("CGEventCreateMouseEvent returned None")
        
except ImportError as e:
    print(f"Failed to import Quartz: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
