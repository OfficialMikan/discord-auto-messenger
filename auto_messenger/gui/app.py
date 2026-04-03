## File: discord_auto_messenger/auto_messenger/gui/app.py (complete corrected)
"""
GUI Application for Discord Auto Messenger
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import json
import os
import random
from typing import Dict, Any, List
from ttkthemes import ThemedTk

from auto_messenger.core.sender import MessageSender
from auto_messenger.core.config import ConfigManager
from auto_messenger.core.logger import Logger
from auto_messenger.utils.helpers import load_messages, validate_discord_id


class AutoMessengerGUI:
    """Main GUI Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Mikan's Discord Auto Messenger v1.0.0")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.logger = Logger()
        
        # Show welcome ASCII art in terminal FIRST
        self.show_welcome_ascii()
        
        # Initialize sender AFTER config is loaded
        self.sender = MessageSender(self.config)
        
        # State variables
        self.name_cache = {}  # id → friendly name
        self.running = False
        self.thread = None
        self.total_sent = 0
        self.cycle_sent = 0
        self.messages = load_messages()
        self.prevent_auto_dry_run = False  # Flag to prevent auto dry-run when editing
        
        # Build UI
        self.build_gui()
        
        # Refresh names AFTER GUI is built
        self.root.after(100, self.refresh_names)  # Delay slightly to ensure GUI is ready
        
        # Apply theme
        self.apply_theme()

    
    def show_welcome_ascii(self):
        """Show welcome ASCII art"""
        ascii_art = r"""
    MMMMMMMM               MMMMMMMMIIIIIIIIIIKKKKKKKKK    KKKKKKK               AAA               NNNNNNNN        NNNNNNNN
    M:::::::M             M:::::::MI::::::::IK:::::::K    K:::::K              A:::A              N:::::::N       N::::::N
    M::::::::M           M::::::::MI::::::::IK:::::::K    K:::::K             A:::::A             N::::::::N      N::::::N
    M:::::::::M         M:::::::::MII::::::IIK:::::::K   K::::::K            A:::::::A            N:::::::::N     N::::::N
    M::::::::::M       M::::::::::M  I::::I  KK::::::K  K:::::KKK           A:::::::::A           N::::::::::N    N::::::N
    M:::::::::::M     M:::::::::::M  I::::I    K:::::K K:::::K             A:::::A:::::A          N:::::::::::N   N::::::N
    M:::::::M::::M   M::::M:::::::M  I::::I    K::::::K:::::K             A:::::A A:::::A         N:::::::N::::N  N::::::N
    M::::::M M::::M M::::M M::::::M  I::::I    K:::::::::::K             A:::::A   A:::::A        N::::::N N::::N N::::::N
    M::::::M  M::::M::::M  M::::::M  I::::I    K:::::::::::K            A:::::A     A:::::A       N::::::N  N::::N:::::::N
    M::::::M   M:::::::M   M::::::M  I::::I    K::::::K:::::K          A:::::AAAAAAAAA:::::A      N::::::N   N:::::::::::N
    M::::::M    M:::::M    M::::::M  I::::I    K:::::K K:::::K        A:::::::::::::::::::::A     N::::::N    N::::::::::N
    M::::::M     MMMMM     M::::::M  I::::I  KK::::::K  K:::::KKK    A:::::AAAAAAAAAAAAA:::::A    N::::::N     N:::::::::N
    M::::::M               M::::::MII::::::IIK:::::::K   K::::::K   A:::::A             A:::::A   N::::::N      N::::::::N
    M::::::M               M::::::MI::::::::IK:::::::K    K:::::K  A:::::A               A:::::A  N::::::N       N:::::::N
    M::::::M               M::::::MI::::::::IK:::::::K    K:::::K A:::::A                 A:::::A N::::::N        N::::::N
    MMMMMMMM               MMMMMMMMIIIIIIIIIIKKKKKKKKK    KKKKKKKAAAAAAA                   AAAAAAANNNNNNNN         NNNNNNN
        """
        # Print to terminal/console first
        print(ascii_art)
        print("=" * 50)
        print("Mikan's Discord Auto Messenger v1.0.0")
        print("=" * 50)
        
        # Then log to GUI
        self.logger.info("Welcome to Mikan's Discord Auto Messenger!")
        self.logger.info("=" * 50)
        
        # Show message count
        msg_count = len(self.messages) if hasattr(self, 'messages') else 0
        print(f"Loaded {msg_count} messages")
        self.logger.info(f"Loaded {msg_count} messages")


    
    def build_gui(self):
        """Build the GUI components"""
        # === Menu Bar ===
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Logs", command=self.export_logs)
        file_menu.add_command(label="Backup Config", command=self.backup_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_theme)
        
        # === Top Control Panel ===
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top, text="▶ Start", command=self.start_sender).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="⏹ Stop", command=self.stop_sender).pack(side=tk.LEFT, padx=5)
        
        self.dry_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Dry Run (Preview Only)", variable=self.dry_var).pack(side=tk.LEFT, padx=20)
        
        ttk.Label(top, text="Delay (sec):").pack(side=tk.LEFT)
        self.delay_var = tk.IntVar(value=self.config.get("delay", 15))
        ttk.Entry(top, textvariable=self.delay_var, width=6).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(top, text="Cycle Sleep (sec):").pack(side=tk.LEFT)
        self.cycle_var = tk.IntVar(value=self.config.get("cycle_sleep", 300))
        ttk.Entry(top, textvariable=self.cycle_var, width=6).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top, text="Apply Settings", command=self.apply_settings).pack(side=tk.LEFT, padx=10)
        
        # Stats
        self.stats_label = ttk.Label(top, text="Sent this cycle: 0 | Total: 0")
        self.stats_label.pack(side=tk.RIGHT)
        
        # === Targets Panel ===
        targets_frame = ttk.LabelFrame(self.root, text="Targets (with real names)")
        targets_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        self.target_list = tk.Listbox(targets_frame, height=8)
        self.target_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(targets_frame)
        btn_frame.pack(fill=tk.X, padx=5)
        ttk.Button(btn_frame, text="Add Target", command=self.gui_add_target).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.gui_remove_target).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh Names", command=self.refresh_names).pack(side=tk.LEFT, padx=5)


        
        # === Messages Editor ===
        msg_frame = ttk.LabelFrame(self.root, text="Messages Editor")
        msg_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        # Create notebook for tabs
        msg_notebook = ttk.Notebook(msg_frame)
        msg_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text messages tab
        text_frame = ttk.Frame(msg_notebook)
        msg_notebook.add(text_frame, text="Text Messages")
        
        self.msg_text_area = scrolledtext.ScrolledText(text_frame, height=8)
        self.msg_text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.msg_text_area.insert(tk.END, self._format_messages_for_editor())
        self.msg_text_area.bind('<KeyRelease>', self.on_message_edit)  # Bind to key release
        
        # Embed builder tab
        embed_frame = ttk.Frame(msg_notebook)
        msg_notebook.add(embed_frame, text="Embed Builder")
        
        ttk.Label(embed_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.embed_title = ttk.Entry(embed_frame, width=50)
        self.embed_title.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(embed_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.embed_desc = scrolledtext.ScrolledText(embed_frame, height=5, width=50)
        self.embed_desc.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(embed_frame, text="Color (Decimal):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.embed_color = ttk.Entry(embed_frame, width=20)
        self.embed_color.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.embed_color.insert(0, "3447003")
        
        ttk.Button(embed_frame, text="Add to Messages", command=self.add_embed_to_messages).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Save messages button
        ttk.Button(msg_frame, text="Save Messages", command=self.save_messages_from_editor).pack(pady=5)
        
        # === Progress Bar ===
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, expand=True, padx=10)
        
        # === Live Stats ===
        stats_frame = ttk.LabelFrame(self.root, text="Live Statistics")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_vars = {
            "cycles": tk.StringVar(value="Cycles Completed: 0"),
            "messages": tk.StringVar(value="Messages Sent: 0"),
            "success": tk.StringVar(value="Success Rate: 100%"),
            "last_send": tk.StringVar(value="Last Send: Never")
        }
        
        row = 0
        for key, var in self.stats_vars.items():
            ttk.Label(stats_frame, textvariable=var).grid(row=row//3, column=row%3, padx=10, pady=2, sticky=tk.W)
            row += 1
        
        # === Log Viewer ===
        log_frame = ttk.LabelFrame(self.root, text="Live Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Redirect logger output to GUI
        self.setup_logger_redirect()
        
        self.logger.info("GUI ready. Use buttons to manage targets and start sending.")
    
    def on_message_edit(self, event=None):
        """Handle message editing - prevent auto dry-run during active editing"""
        if self.running and not self.prevent_auto_dry_run:
            # Temporarily disable auto dry-run to prevent spam
            self.prevent_auto_dry_run = True
            self.root.after(2000, self.enable_auto_dry_run)  # Re-enable after 2 seconds of no typing
    
    def enable_auto_dry_run(self):
        """Re-enable auto dry-run after editing pause"""
        self.prevent_auto_dry_run = False
    
    def setup_logger_redirect(self):
        """Redirect logger output to GUI log viewer"""
        class GUILogger:
            def __init__(self, text_widget):
                self.text_widget = text_widget
                self.closed = False
            
            def write(self, message):
                try:
                    if self.text_widget and not self.closed:
                        self.text_widget.insert(tk.END, message)
                        self.text_widget.see(tk.END)
                except:
                    # GUI might be closed, ignore errors
                    self.closed = True
                    # Print to console instead
                    print(message, end='')
            
            def flush(self):
                pass
        
        import sys
        sys.stdout = GUILogger(self.log_text)

    
    def apply_theme(self):
        """Apply GUI theme"""
        theme = self.config.get("theme", "arc")
        try:
            self.root.set_theme(theme)
        except:
            pass  # Fallback to default theme
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        current = self.config.get("theme", "arc")
        new_theme = "breeze" if current == "arc" else "arc"
        self.config["theme"] = new_theme
        self.config_manager.save_config(self.config)
        self.apply_theme()
    
    def _format_messages_for_editor(self) -> str:
        """Format messages for text editor"""
        result = []
        for msg in self.messages:
            if msg["type"] == "text":
                result.append(msg["data"])
            else:
                result.append(json.dumps(msg["data"], indent=2))
            result.append("")  # Double newline separator
        return "\n".join(result)
    
    def save_messages_from_editor(self):
        """Save messages from editor to file"""
        content = self.msg_text_area.get(1.0, tk.END).strip()
        try:
            with open("messages.txt", "w", encoding="utf-8") as f:
                f.write(content)
            self.messages = load_messages()
            self.logger.success("Messages saved successfully!")
            # Refresh channel settings UI
        except Exception as e:
            self.logger.error(f"Failed to save messages: {e}")
    
    def add_embed_to_messages(self):
        """Add embed to messages editor"""
        title = self.embed_title.get().strip()
        desc = self.embed_desc.get(1.0, tk.END).strip()
        color = self.embed_color.get().strip()
        
        if not title:
            messagebox.showwarning("Missing Field", "Please enter a title for the embed")
            return
            
        embed_json = {
            "title": title,
            "description": desc if desc else " ",
            "color": int(color) if color.isdigit() else 3447003
        }
        
        # Add to editor
        current = self.msg_text_area.get(1.0, tk.END).strip()
        if current:
            current += "\n\n"
        current += json.dumps(embed_json, indent=2)
        self.msg_text_area.delete(1.0, tk.END)
        self.msg_text_area.insert(1.0, current)
    
    def export_logs(self):
        """Export logs to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open("auto_log.txt", "r") as src, open(filename, "w") as dst:
                    dst.write(src.read())
                self.logger.success(f"Logs exported to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to export logs: {e}")
    
    def backup_config(self):
        """Backup configuration file"""
        self.config_manager.backup_config()
    
    def refresh_names(self):
        """Refresh target names"""
        # Save current selection if any
        current_selection = self.target_list.curselection()
        
        self.target_list.delete(0, tk.END)
        self.name_cache.clear()
        
        token = self.config.get("token")
        if not token:
            self.logger.warning("No token set yet.")
            return
            
        for t in self.config.get("targets", []):
            # Just pass the channel ID, the sender will figure out the type internally
            name = self.sender.fetch_channel_name(t["id"])
            self.name_cache[t["id"]] = name
            ttype = "Channel" if t["type"] == "channel" else "DM"
            self.target_list.insert(tk.END, f"[{ttype}] {t['id']} → {name}")
        
        # Restore selection if possible
        if current_selection and len(current_selection) > 0:
            idx = current_selection[0]
            if idx < self.target_list.size():
                self.target_list.selection_set(idx)
    
    def gui_add_target(self):
        """Open dialog to add target"""
        win = tk.Toplevel(self.root)
        win.title("Add Target")
        win.geometry("300x200")
        
        tk.Label(win, text="Type:").pack(pady=5)
        type_var = tk.StringVar(value="channel")
        ttk.Radiobutton(win, text="Channel", variable=type_var, value="channel").pack()
        ttk.Radiobutton(win, text="User (DM)", variable=type_var, value="dm").pack()
        
        tk.Label(win, text="ID:").pack(pady=5)
        id_entry = ttk.Entry(win, width=30)
        id_entry.pack()
        
        def add():
            tid = id_entry.get().strip()
            if not tid:
                messagebox.showwarning("Empty ID", "Please enter a target ID")
                return
                
            if not validate_discord_id(tid):
                messagebox.showerror("Invalid ID", "Please enter a valid Discord ID (17-20 digits)")
                return
                
            # Add to config
            self.config.setdefault("targets", []).append({"type": type_var.get(), "id": tid})
            self.config_manager.save_config(self.config)
            self.refresh_names()
            self.logger.success(f"Added new {type_var.get()}: {tid}")
            win.destroy()
            
        ttk.Button(win, text="Add", command=add).pack(pady=10)
        
        # Add explanation
        tk.Label(win, text="Note: For DMs, use the User ID,\nnot a channel ID", 
                 fg="blue", font=("Arial", 8)).pack(pady=5)
    
    def gui_remove_target(self):
        """Remove selected target"""
        sel = self.target_list.curselection()
        if not sel:
            messagebox.showwarning("Nothing selected", "Select a target first")
            return
        idx = sel[0]
        if idx < len(self.config.get("targets", [])):
            target_id = self.config["targets"][idx]["id"]
            del self.config["targets"][idx]
            # Also remove channel-specific settings
            if "channel_messages" in self.config and target_id in self.config["channel_messages"]:
                del self.config["channel_messages"][target_id]
            self.config_manager.save_config(self.config)
            self.refresh_names()
            self.hide_channel_settings()  # Hide settings panel after removal
            self.logger.info("Target removed.")

    
    def apply_settings(self):
        """Apply GUI settings to config"""
        self.config["delay"] = self.delay_var.get()
        self.config["cycle_sleep"] = self.cycle_var.get()
        self.config_manager.save_config(self.config)
        self.logger.success(f"Settings applied → Delay: {self.delay_var.get()}s | Cycle: {self.cycle_var.get()}s")
    
    def start_sender(self):
        """Start message sending loop"""
        if self.running:
            self.logger.warning("Already running!")
            return
        if not self.config.get("token") or not self.config.get("targets"):
            self.logger.error("Error: Token or targets missing!")
            return
        if not self.messages:
            self.logger.error("Error: No messages in messages.txt!")
            return
        
        self.running = True
        self.cycle_sent = 0
        self.progress_bar.start()
        self.thread = threading.Thread(target=self.sender_loop, daemon=True)
        self.thread.start()
        self.logger.success("🚀 Auto sender STARTED")
    
    def stop_sender(self):
        """Stop message sending loop"""
        self.running = False
        self.progress_bar.stop()
        self.progress_label.config(text="Stopped")
        self.logger.info("⛔ Auto sender STOPPED")
    
    def sender_loop(self):
        """Main sending loop"""
        delay = self.delay_var.get()
        cycle_sleep = self.cycle_var.get()
        dry = self.dry_var.get()
        token = self.config["token"]
        cycles_completed = 0
        
        while self.running:
            self.progress_label.config(text="Sending messages...")
            cycle_start_time = time.time()
            cycle_success_count = 0
            total_attempts = 0
            
            # Send all messages to all targets
            for item in self.messages:
                if not self.running:
                    break
                    
                for t in self.config.get("targets", []):
                    if not self.running:
                        break
                        
                    # Skip channels in cooldown
                    if hasattr(self.sender, 'is_channel_cooldown') and self.sender.is_channel_cooldown(t["id"]):
                        self.logger.info(f"Skipping {t['id']} - in cooldown")
                        continue
                        
                    name = self.name_cache.get(t["id"], t["id"])
                    # Pass the target type to send_message
                    success = self.sender.send_message(t["id"], name, item, dry, t.get("type", "channel"))
                    
                    total_attempts += 1
                    if success:
                        self.cycle_sent += 1
                        self.total_sent += 1
                        cycle_success_count += 1
                    
                    # Update progress
                    self.root.after(0, lambda s=self.cycle_sent: self.stats_label.config(
                        text=f"Sent this cycle: {s} | Total: {self.total_sent}"))
                    
                    # Small delay between messages (minimum 1 second)
                    if self.running:
                        time.sleep(max(1, random.uniform(delay * 0.7, delay * 1.4)))
            
            if self.running:
                cycles_completed += 1
                cycle_duration = time.time() - cycle_start_time
                success_rate = (cycle_success_count / total_attempts * 100) if total_attempts > 0 else 100
                
                # Update stats
                self.root.after(0, lambda c=cycles_completed, m=self.total_sent, s=success_rate: [
                    self.stats_vars["cycles"].set(f"Cycles Completed: {c}"),
                    self.stats_vars["messages"].set(f"Messages Sent: {m}"),
                    self.stats_vars["success"].set(f"Success Rate: {s:.1f}%"),
                    self.stats_vars["last_send"].set(f"Last Send: {time.strftime('%H:%M:%S')}")
                ])
                
                self.logger.success(f"✅ Cycle completed — {self.cycle_sent} messages sent this cycle "
                                f"({cycle_duration:.1f}s, {success_rate:.1f}% success)")
                self.cycle_sent = 0
                self.progress_label.config(text="Waiting for next cycle...")
                time.sleep(max(30, cycle_sleep + random.randint(10, 60)))  # Minimum 30 sec cycle sleep



# Make sure the class is accessible when imported
__all__ = ['AutoMessengerGUI']
