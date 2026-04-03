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
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)

    print("Starting Mikan's Discord Auto Messenger v1.0.0...")
    
    # Check if config exists
    config_path = os.path.join(base_dir, "config.json")
    if not os.path.exists(config_path):
        print("❌ Config file not found. Creating config.json from template...")
        template_path = os.path.join(base_dir, "config_template.json")
        if os.path.exists(template_path):
            try:
                import shutil
                shutil.copyfile(template_path, config_path)
                print("✅ config.json created from template.")
                print("Please edit config.json with your Discord token, targets, and settings.")
            except Exception as e:
                print(f"Failed to create config.json: {e}")
        else:
            print("Template not found. Create config.json manually with this content:")
            print('{')
            print('  "token": "YOUR_DISCORD_TOKEN_HERE",')
            print('  "targets": [],')
            print('  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",')
            print('  "delay": 15,')
            print('  "cycle_sleep": 300,')
            print('  "theme": "arc"')
            print('}')

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
