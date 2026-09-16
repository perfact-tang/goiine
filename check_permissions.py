import ApplicationServices
import sys

def check_accessibility():
    trusted = ApplicationServices.AXIsProcessTrusted()
    print(f"Accessibility Trusted: {trusted}")
    if not trusted:
        print("---")
        print("WARNING: This app does not have permission to control the mouse.")
        print("macOS is blocking the mouse events.")
        print("---")
        print("Please follow these steps EXACTLY:")
        print("1. Go to System Settings > Privacy & Security > Accessibility")
        print("2. Find your Terminal / Editor in the list.")
        print("3. Click the '-' (minus) button to remove it.")
        print("4. Run this script again.")
        print("5. A popup should appear asking for permission. Click 'Open System Settings' and turn it ON.")
        
        # Attempt to prompt user
        options = {dict(ApplicationServices.kAXTrustedCheckOptionPrompt): True}
        ApplicationServices.AXIsProcessTrustedWithOptions(options)
    else:
        print("SUCCESS: App is trusted. Mouse control should work.")

if __name__ == "__main__":
    check_accessibility()
