## File: discord_auto_messenger/auto_messenger/gui/app.py (complete corrected)
"""
Modern GUI Application for Discord Auto Messenger using PyQt6
"""
import sys
import json
import time
import random
import os
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QListWidget, QComboBox,
    QSpinBox, QCheckBox, QGroupBox, QTabWidget, QSplitter, QMessageBox,
    QProgressBar, QStatusBar, QFrame, QDialog, QFormLayout, QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QPalette, QColor

from auto_messenger.core.sender import MessageSender
from auto_messenger.core.config import ConfigManager
from auto_messenger.core.logger import get_logger
from auto_messenger.utils.helpers import load_messages, validate_discord_id


class SenderWorker(QThread):
    """Worker thread for message sending to avoid UI blocking"""
    update_stats = pyqtSignal(dict)
    update_log = pyqtSignal(str)
    finished_cycle = pyqtSignal()

    def __init__(self, sender, config, messages):
        super().__init__()
        self.sender = sender
        self.config = config
        self.messages = messages
        self.running = False

    def run(self):
        self.running = True
        delay = self.config.get("delay", 15)
        cycle_sleep = self.config.get("cycle_sleep", 300)

        while self.running:
            cycle_start_time = time.time()
            cycle_success_count = 0
            total_attempts = 0

            for item in self.messages:
                if not self.running:
                    break

                for t in self.config.get("targets", []):
                    if not self.running:
                        break

                    if hasattr(self.sender, 'is_channel_cooldown') and self.sender.is_channel_cooldown(t["id"]):
                        self.update_log.emit(f"Skipping {t['id']} - in cooldown")
                        continue

                    name = self.sender.fetch_channel_name(t["id"])
                    success = self.sender.send_message(t["id"], name, item, False, t.get("type", "channel"))

                    total_attempts += 1
                    if success:
                        cycle_success_count += 1

                    if self.running:
                        time.sleep(max(1, random.uniform(delay * 0.7, delay * 1.4)))

            if self.running:
                cycle_duration = time.time() - cycle_start_time
                success_rate = (cycle_success_count / total_attempts * 100) if total_attempts > 0 else 100

                stats = {
                    "cycles": "Cycles Completed: 1",
                    "messages": f"Messages Sent: {cycle_success_count}",
                    "success": f"Success Rate: {success_rate:.1f}%",
                    "last_send": f"Last Send: {time.strftime('%H:%M:%S')}"
                }
                self.update_stats.emit(stats)
                self.update_log.emit(f"✅ Cycle completed — {cycle_success_count} messages sent ({cycle_duration:.1f}s, {success_rate:.1f}% success)")
                self.finished_cycle.emit()
                time.sleep(max(30, cycle_sleep + random.randint(10, 60)))

    def stop(self):
        self.running = False


class AutoMessengerGUI(QMainWindow):
    """Modern GUI Application using PyQt6"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.logger = get_logger()
        self.sender = MessageSender(self.config)
        self.worker = None
        self.name_cache = {}
        self.messages = load_messages()
        self.total_sent = 0
        self.cycle_sent = 0

        self.init_ui()
        self.load_config()
        self.refresh_names()

    
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


    
    def init_ui(self):
        """Initialize the PyQt6 GUI"""
        self.setWindowTitle("Mikan's Discord Auto Messenger v1.0.0")
        self.setGeometry(100, 100, 1000, 800)
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Menu bar
        self.create_menu_bar()
        
        # Bot Configuration
        config_group = QGroupBox("Bot Configuration")
        config_layout = QFormLayout(config_group)
        
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setText(self.config.get("token", ""))
        config_layout.addRow("Token:", self.token_edit)
        
        save_token_btn = QPushButton("Save Token")
        save_token_btn.clicked.connect(self.update_token)
        config_layout.addRow(save_token_btn)
        
        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setText(self.config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"))
        config_layout.addRow("User-Agent:", self.user_agent_edit)
        
        save_ua_btn = QPushButton("Save User-Agent")
        save_ua_btn.clicked.connect(self.update_user_agent)
        config_layout.addRow(save_ua_btn)
        
        main_layout.addWidget(config_group)
        
        # Control Panel
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.start_sender)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_sender)
        control_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("🧹 Clear Logs")
        self.clear_btn.clicked.connect(self.clear_log_view)
        control_layout.addWidget(self.clear_btn)
        
        self.dry_check = QCheckBox("Dry Run (Preview Only)")
        control_layout.addWidget(self.dry_check)
        
        control_layout.addWidget(QLabel("Delay (sec):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setValue(self.config.get("delay", 15))
        control_layout.addWidget(self.delay_spin)
        
        control_layout.addWidget(QLabel("Cycle Sleep (sec):"))
        self.cycle_spin = QSpinBox()
        self.cycle_spin.setValue(self.config.get("cycle_sleep", 300))
        control_layout.addWidget(self.cycle_spin)
        
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self.apply_settings)
        control_layout.addWidget(apply_btn)
        
        self.stats_label = QLabel("Sent this cycle: 0 | Total: 0")
        control_layout.addStretch()
        control_layout.addWidget(self.stats_label)
        
        main_layout.addLayout(control_layout)
        
        # Targets Panel
        targets_group = QGroupBox("Targets (with real names)")
        targets_layout = QVBoxLayout(targets_group)
        
        self.target_list = QListWidget()
        targets_layout.addWidget(self.target_list)
        
        targets_btn_layout = QHBoxLayout()
        add_target_btn = QPushButton("Add Target")
        add_target_btn.clicked.connect(self.gui_add_target)
        targets_btn_layout.addWidget(add_target_btn)
        
        remove_target_btn = QPushButton("Remove Selected")
        remove_target_btn.clicked.connect(self.gui_remove_target)
        targets_btn_layout.addWidget(remove_target_btn)
        
        refresh_btn = QPushButton("Refresh Names")
        refresh_btn.clicked.connect(self.refresh_names)
        targets_btn_layout.addWidget(refresh_btn)
        
        targets_layout.addLayout(targets_btn_layout)
        main_layout.addWidget(targets_group)
        
        # Messages Editor
        messages_group = QGroupBox("Messages Editor")
        messages_layout = QVBoxLayout(messages_group)
        
        self.tab_widget = QTabWidget()
        messages_layout.addWidget(self.tab_widget)
        
        # Text Messages Tab
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        self.msg_text_edit = QTextEdit()
        self.msg_text_edit.setPlainText(self._format_messages_for_editor())
        self.msg_text_edit.textChanged.connect(self.on_message_edit)
        text_layout.addWidget(self.msg_text_edit)
        self.tab_widget.addTab(text_tab, "Text Messages")
        
        # Embed Builder Tab
        embed_tab = QWidget()
        embed_layout = QFormLayout(embed_tab)
        
        self.embed_title_edit = QLineEdit()
        embed_layout.addRow("Title:", self.embed_title_edit)
        
        self.embed_desc_edit = QTextEdit()
        embed_layout.addRow("Description:", self.embed_desc_edit)
        
        self.embed_color_edit = QLineEdit("3447003")
        embed_layout.addRow("Color (Decimal):", self.embed_color_edit)
        
        add_embed_btn = QPushButton("Add to Messages")
        add_embed_btn.clicked.connect(self.add_embed_to_messages)
        embed_layout.addRow(add_embed_btn)
        
        self.tab_widget.addTab(embed_tab, "Embed Builder")
        
        save_msg_btn = QPushButton("Save Messages")
        save_msg_btn.clicked.connect(self.save_messages_from_editor)
        messages_layout.addWidget(save_msg_btn)
        
        main_layout.addWidget(messages_group)
        
        # Progress Bar
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)
        
        # Live Stats
        stats_group = QGroupBox("Live Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.stats_labels = {}
        stats_items = ["Cycles Completed", "Messages Sent", "Success Rate", "Last Send"]
        for i, item in enumerate(stats_items):
            label = QLabel(f"{item}: 0")
            self.stats_labels[item.lower().replace(" ", "_")] = label
            stats_layout.addWidget(label, i // 2, i % 2)
        
        main_layout.addWidget(stats_group)
        
        # Log Viewer
        log_group = QGroupBox("Live Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        log_layout.addWidget(self.log_text_edit)
        main_layout.addWidget(log_group)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("GUI ready. Use buttons to manage targets and start sending.")
        
        # Connect worker signals
        if self.worker:
            self.worker.update_stats.connect(self.update_stats)
            self.worker.update_log.connect(self.update_log)
            self.worker.finished_cycle.connect(self.on_cycle_finished)
        
        self.logger.info("GUI initialized successfully.")
    
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(palette)
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Export Logs", self.export_logs)
        file_menu.addAction("Backup Config", self.backup_config)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Toggle Dark Mode", self.toggle_theme)
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        # For simplicity, just toggle dark mode
        if self.palette().color(QPalette.ColorRole.Window) == QColor(53, 53, 53):
            self.setPalette(QApplication.style().standardPalette())
        else:
            self.apply_dark_theme()
    
    def gui_remove_target(self):
        """Remove selected target"""
        current_item = self.target_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a target to remove.")
            return
        
        text = current_item.text()
        # Extract ID from text like "[Channel] 123 → name"
        import re
        match = re.search(r'\] (\d+) →', text)
        if match:
            tid = match.group(1)
            self.config["targets"] = [t for t in self.config.get("targets", []) if t["id"] != tid]
            self.config_manager.save_config(self.config)
            self.refresh_names()
            self.logger.info(f"Removed target: {tid}")
    
    def start_sender(self):
        """Start the message sender"""
        if self.worker and self.worker.isRunning():
            return
        self.worker = SenderWorker(self.sender, self.config, self.messages)
        self.worker.update_stats.connect(self.update_stats)
        self.worker.update_log.connect(self.update_log)
        self.worker.finished_cycle.connect(self.on_cycle_finished)
        self.worker.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.logger.info("Message sender started.")
    
    def stop_sender(self):
        """Stop the message sender"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.logger.info("Message sender stopped.")
    
    def apply_settings(self):
        """Apply delay and cycle settings"""
        self.config["delay"] = self.delay_spin.value()
        self.config["cycle_sleep"] = self.cycle_spin.value()
        self.config_manager.save_config(self.config)
        self.logger.info("Settings applied.")
    
    def update_stats(self, stats):
        """Update statistics display"""
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].setText(f"{key.replace('_', ' ').title()}: {value}")
    
    def update_log(self, message):
        """Update log display"""
        self.log_text_edit.append(message)
    
    def on_cycle_finished(self):
        """Handle cycle finished"""
        pass
    
    def on_message_edit(self):
        """Handle message editing"""
        pass
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
        
        # === Bot Configuration ===
        config_panel = ttk.LabelFrame(self.root, text="Bot Configuration")
        config_panel.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(config_panel, text="Token:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.token_var = tk.StringVar(value=self.config.get("token", ""))
        ttk.Entry(config_panel, textvariable=self.token_var, width=70, show="*").grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(config_panel, text="Save Token", command=self.update_token).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(config_panel, text="User-Agent:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.user_agent_var = tk.StringVar(value=self.config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"))
        ttk.Entry(config_panel, textvariable=self.user_agent_var, width=70).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(config_panel, text="Save User-Agent", command=self.update_user_agent).grid(row=1, column=2, padx=5, pady=2)

        # === Top Control Panel ===
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top, text="▶ Start", command=self.start_sender).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="⏹ Stop", command=self.stop_sender).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="🧹 Clear Logs", command=self.clear_log_view).pack(side=tk.LEFT, padx=5)
        
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

    def update_token(self):
        """Update bot token from GUI field"""
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Missing Token", "Please enter a valid Discord token.")
            return
        self.config["token"] = token
        self.config_manager.save_config(self.config)
        self.sender.session.headers["Authorization"] = token
        self.logger.info("Token updated and saved.")

    def update_user_agent(self):
        """Update user-agent setting"""
        user_agent = self.user_agent_edit.text().strip()
        if not user_agent:
            QMessageBox.warning(self, "Missing User-Agent", "Please enter a valid User-Agent string.")
            return
        self.config["user_agent"] = user_agent
        self.config_manager.save_config(self.config)
        self.sender.session.headers["User-Agent"] = user_agent
        self.logger.info("User-Agent updated and saved.")

    def clear_log_view(self):
        """Clear GUI log text content"""
        self.log_text_edit.clear()
        self.logger.info("Log window cleared.")

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
        content = self.msg_text_edit.toPlainText()
        try:
            app_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            messages_file = os.path.join(app_dir, "messages.txt")
            with open(messages_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.messages = load_messages()
            self.logger.info("Messages saved successfully!")
        except Exception as e:
            self.logger.error(f"Failed to save messages: {e}")
    
    def add_embed_to_messages(self):
        """Add embed to messages editor"""
        title = self.embed_title_edit.text().strip()
        desc = self.embed_desc_edit.toPlainText().strip()
        color = self.embed_color_edit.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Missing Field", "Please enter a title for the embed")
            return
            
        embed_json = {
            "title": title,
            "description": desc if desc else " ",
            "color": int(color) if color.isdigit() else 3447003
        }
        
        # Add to editor
        current = self.msg_text_edit.toPlainText()
        if current:
            current += "\n\n"
        current += json.dumps(embed_json, indent=2)
        self.msg_text_edit.setPlainText(current)
    
    def export_logs(self):
        """Export logs to file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Export Logs", "", "Text files (*.txt);;All files (*)")
            if filename:
                app_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
                log_file = os.path.join(app_dir, "auto_log.txt")
                with open(log_file, "r") as src, open(filename, "w") as dst:
                    dst.write(src.read())
                self.logger.info(f"Logs exported to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to export logs: {e}")
    
    def backup_config(self):
        """Backup configuration file"""
        self.config_manager.backup_config()
    
    def refresh_names(self):
        """Refresh target names"""
        self.target_list.clear()
        self.name_cache.clear()
        
        token = self.config.get("token")
        if not token:
            self.logger.warning("No token set yet.")
            return
            
        for t in self.config.get("targets", []):
            name = self.sender.fetch_channel_name(t["id"])
            self.name_cache[t["id"]] = name
            ttype = "Channel" if t["type"] == "channel" else "DM"
            self.target_list.addItem(f"[{ttype}] {t['id']} → {name}")
    
    def gui_add_target(self):
        """Open dialog to add target"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Target")
        dialog.setModal(True)
        
        layout = QFormLayout(dialog)
        
        type_combo = QComboBox()
        type_combo.addItems(["channel", "dm"])
        layout.addRow("Type:", type_combo)
        
        id_edit = QLineEdit()
        layout.addRow("ID:", id_edit)
        
        buttons = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(lambda: self._add_target(dialog, type_combo.currentText(), id_edit.text()))
        buttons.addWidget(add_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addRow(buttons)
        
        dialog.exec()
    
    def _add_target(self, dialog, ttype, tid):
        tid = tid.strip()
        if not tid:
            QMessageBox.warning(dialog, "Empty ID", "Please enter a target ID")
            return
            
        if not validate_discord_id(tid):
            QMessageBox.warning(dialog, "Invalid ID", "Please enter a valid Discord ID (17-20 digits)")
            return
            
        # Add to config
        self.config.setdefault("targets", []).append({"type": ttype, "id": tid})
        self.config_manager.save_config(self.config)
        self.refresh_names()
        self.logger.info(f"Added new {ttype}: {tid}")
        dialog.accept()
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



    def apply_modern_style(self):
        """Apply modern dark theme styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QLineEdit, QTextEdit, QListWidget {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
            QCheckBox {
                color: white;
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)

    def load_config(self):
        """Load configuration into UI"""
        self.token_edit.setText(self.config.get("token", ""))
        self.ua_edit.setText(self.config.get("user_agent", ""))

    def save_token(self):
        """Save token to config"""
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Missing Token", "Please enter a valid Discord token.")
            return
        self.config["token"] = token
        self.config_manager.save_config(self.config)
        self.sender.session.headers["Authorization"] = token
        self.status_bar.showMessage("Token saved", 3000)

    def save_user_agent(self):
        """Save user-agent to config"""
        ua = self.ua_edit.text().strip()
        if not ua:
            QMessageBox.warning(self, "Missing User-Agent", "Please enter a valid User-Agent string.")
            return
        self.config["user_agent"] = ua
        self.config_manager.save_config(self.config)
        self.sender.session.headers["User-Agent"] = ua
        self.status_bar.showMessage("User-Agent saved", 3000)

    def apply_settings(self):
        """Apply settings to config"""
        self.config["delay"] = self.delay_spin.value()
        self.config["cycle_sleep"] = self.cycle_spin.value()
        self.config_manager.save_config(self.config)
        self.status_bar.showMessage("Settings applied", 3000)

    def start_sender(self):
        """Start the sender worker"""
        if self.worker and self.worker.isRunning():
            self.status_bar.showMessage("Already running", 3000)
            return
        if not self.config.get("token") or not self.config.get("targets"):
            QMessageBox.warning(self, "Configuration Error", "Token or targets missing!")
            return
        if not self.messages:
            QMessageBox.warning(self, "Configuration Error", "No messages in messages.txt!")
            return

        self.worker = SenderWorker(self.sender, self.config, self.messages)
        self.worker.update_stats.connect(self.update_stats)
        self.worker.update_log.connect(self.append_log)
        self.worker.finished_cycle.connect(self.on_cycle_finished)
        self.worker.start()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_bar.showMessage("Started")

    def stop_sender(self):
        """Stop the sender worker"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Stopped")

    def clear_log(self):
        """Clear the log"""
        self.log_edit.clear()
        self.status_bar.showMessage("Log cleared", 3000)

    def add_target(self):
        """Add a new target"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Target")
        layout = QFormLayout(dialog)

        type_combo = QComboBox()
        type_combo.addItems(["channel", "dm"])
        layout.addRow("Type:", type_combo)

        id_edit = QLineEdit()
        layout.addRow("ID:", id_edit)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Add")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            tid = id_edit.text().strip()
            if not tid or not validate_discord_id(tid):
                QMessageBox.warning(self, "Invalid ID", "Please enter a valid Discord ID (17-20 digits)")
                return
            self.config.setdefault("targets", []).append({"type": type_combo.currentText(), "id": tid})
            self.config_manager.save_config(self.config)
            self.refresh_names()

    def remove_target(self):
        """Remove selected target"""
        current_row = self.targets_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Select a target first")
            return
        if current_row < len(self.config.get("targets", [])):
            del self.config["targets"][current_row]
            self.config_manager.save_config(self.config)
            self.refresh_names()

    def refresh_names(self):
        """Refresh target names"""
        self.targets_list.clear()
        self.name_cache.clear()

        token = self.config.get("token")
        if not token:
            self.status_bar.showMessage("No token set", 3000)
            return

        for t in self.config.get("targets", []):
            name = self.sender.fetch_channel_name(t["id"])
            self.name_cache[t["id"]] = name
            ttype = "Channel" if t["type"] == "channel" else "DM"
            self.targets_list.addItem(f"[{ttype}] {t['id']} → {name}")

    def format_messages(self):
        """Format messages for display"""
        result = []
        for msg in self.messages:
            if msg["type"] == "text":
                result.append(msg["data"])
            else:
                result.append(json.dumps(msg["data"], indent=2))
            result.append("")
        return "\n".join(result)

    def save_messages(self):
        """Save messages from editor"""
        content = self.messages_edit.toPlainText()
        try:
            with open("messages.txt", "w", encoding="utf-8") as f:
                f.write(content)
            self.messages = load_messages()
            self.status_bar.showMessage("Messages saved", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save messages: {e}")

    def add_embed(self):
        """Add embed to messages"""
        title = self.embed_title.text().strip()
        desc = self.embed_desc.toPlainText().strip()
        color = self.embed_color.text().strip()

        if not title:
            QMessageBox.warning(self, "Missing Field", "Please enter a title for the embed")
            return

        embed_json = {
            "title": title,
            "description": desc if desc else " ",
            "color": int(color) if color.isdigit() else 3447003
        }

        current = self.messages_edit.toPlainText()
        if current:
            current += "\n\n"
        current += json.dumps(embed_json, indent=2)
        self.messages_edit.setPlainText(current)

    def update_stats(self, stats):
        """Update stats labels"""
        self.cycles_label.setText(stats.get("cycles", ""))
        self.messages_label.setText(stats.get("messages", ""))
        self.success_label.setText(stats.get("success", ""))
        self.last_send_label.setText(stats.get("last_send", ""))

    def append_log(self, message):
        """Append message to log"""
        self.log_edit.append(message)

    def on_cycle_finished(self):
        """Handle cycle finished"""
        pass

    def update_ui(self):
        """Periodic UI update"""
        self.stats_label.setText(f"Sent this cycle: {self.cycle_sent} | Total: {self.total_sent}")

    def closeEvent(self, event):
        """Handle window close"""
        self.stop_sender()
        event.accept()
