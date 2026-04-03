#!/usr/bin/env python3
"""
Discord Auto Messenger - Main Entry Point
"""
import sys
import os

def maximize_console():
    """Maximize console window"""
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 3)  # SW_MAXIMIZE
        ctypes.windll.user32.SetForegroundWindow(ctypes.windll.kernel32.GetConsoleWindow())
    except:
        pass

def restore_console():
    """Restore console window to normal size"""
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)  # SW_SHOWNORMAL
    except:
        pass

def main():
    """Main entry point"""
    print("Starting Mikan's Discord Auto Messenger v1.0.0...")
    
    # Check if config exists
    if not os.path.exists("config.json"):
        print("❌ Config file not found!")
        print("💡 Run DiscordTokenExtractor.exe first to set up your token")
        print("   or manually create config.json with your Discord token")
        input("Press Enter to exit...")
        return
    
    # Continue with normal startup...
    # [rest of your existing main function]
    
    # Maximize console during loading
    maximize_console()
    
    # Show loading screen
    try:
        from loading_screen import show_loading_screen
        show_loading_screen()
    except ImportError:
        print("Loading...")
        import time
        time.sleep(5)
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Restore console size before GUI starts
    restore_console()
    
    print("Running in GUI mode...")
    try:
        print("Importing GUI modules...")
        from auto_messenger.gui.app import AutoMessengerGUI
        from ttkthemes import ThemedTk
        print("GUI modules imported successfully")
        
        print("Creating GUI window...")
        root = ThemedTk(theme="arc")
        root.title("Mikan's Discord Auto Messenger v1.0.0")
        root.geometry("1200x800")
        print("ThemedTk created")
        
        app = AutoMessengerGUI(root)
        print("AutoMessengerGUI created")
        
        print("Starting mainloop...")
        print("You can minimize this console window - the GUI will continue running")
        root.mainloop()
        print("Application closed successfully")
        
    except ImportError as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()
        print("Make sure all required packages are installed:")
        print("pip install requests cryptography ttkthemes pytest aiohttp")
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"GUI Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
