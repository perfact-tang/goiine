import Quartz
import time
import sys

def test_move():
    print("Testing Mouse Movement using Quartz...")
    print("Please watch your mouse cursor.")
    print("Moving to (100, 100) in 2 seconds...")
    time.sleep(2)
    
    # Try Session Event Tap (User space)
    x, y = 100, 100
    move_event = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (x, y), 0
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move_event)
    
    print("Moved? Now moving to (500, 500) in 1 second...")
    time.sleep(1)
    
    x, y = 500, 500
    move_event = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (x, y), 0
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move_event)
    
    print("Test finished.")
    print("If mouse did not move, you have a PERMISSION issue.")
    print("1. Open System Settings -> Privacy & Security -> Accessibility")
    print("2. REMOVE 'Terminal' or 'Python' (click the - button)")
    print("3. Run this script again.")

if __name__ == "__main__":
    test_move()
