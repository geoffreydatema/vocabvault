import sys
import json
import os
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTabWidget, QLineEdit, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QMessageBox, QGridLayout, QSizePolicy, QLabel,
                               QCheckBox, QSpinBox, QDialog)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class FlashcardDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Practice Mode")
        self.resize(600, 400)
        self.items = items
        self.current_index = 0
        
        # UI Setup
        self.layout = QVBoxLayout(self)
        
        # Progress Label
        self.progress_label = QLabel(f"Card 1 of {len(items)}")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #777; font-size: 14px;")
        self.layout.addWidget(self.progress_label)
        
        # Card Container (Centered)
        self.card_container = QVBoxLayout()
        self.layout.addLayout(self.card_container)
        self.layout.addStretch()
        
        # Russian Text (The Question)
        self.russian_label = QLabel()
        self.russian_label.setAlignment(Qt.AlignCenter)
        self.russian_label.setWordWrap(True)
        self.russian_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        self.card_container.addWidget(self.russian_label)
        
        # Spacing
        self.card_container.addSpacing(20)
        
        # English Text (The Answer)
        self.english_label = QLabel()
        self.english_label.setAlignment(Qt.AlignCenter)
        self.english_label.setWordWrap(True)
        self.english_label.setStyleSheet("font-size: 24px; color: #aaa; font-style: italic;")
        self.card_container.addWidget(self.english_label)
        
        self.layout.addStretch()
        
        # Controls
        self.action_button = QPushButton("Reveal Answer")
        self.action_button.setMinimumHeight(50)
        self.action_button.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.action_button.clicked.connect(self.handle_action)
        self.layout.addWidget(self.action_button)
        
        # Initial State
        self.is_revealed = False
        self.show_card()

    def show_card(self):
        """Display the current card."""
        item = self.items[self.current_index]
        self.russian_label.setText(item['russian'])
        self.english_label.setText(item['english'])
        
        # Hide answer initially
        self.english_label.hide()
        self.is_revealed = False
        
        self.action_button.setText("Reveal Answer")
        self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.items)}")

    def handle_action(self):
        """Handle button click (Reveal or Next)."""
        if not self.is_revealed:
            # Reveal Phase
            self.english_label.show()
            self.is_revealed = True
            if self.current_index < len(self.items) - 1:
                self.action_button.setText("Next Card")
            else:
                self.action_button.setText("Finish")
        else:
            # Next Phase
            if self.current_index < len(self.items) - 1:
                self.current_index += 1
                self.show_card()
            else:
                self.accept() # Close dialog

class VocabVault(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vocab Vault")
        self.resize(1280, 720)
        
        # Global font size
        font = QFont()
        font.setPointSize(14)
        self.setFont(font)
        
        self.filename = "russian.json"
        # The categories correspond to the tab names
        self.categories = ["all words", "all phrases", "all sentences"]
        self.tables = {} # Store references to table widgets
        self.letter_buttons = [] # Store references to keyboard keys for shifting
        self.is_shifted = False
        
        self.data = self.load_data()
        
        self.setup_ui()

    def load_data(self):
        """Loads data from json, or initializes structure if empty."""
        default_data = {cat: [] for cat in self.categories}
        
        if not os.path.exists(self.filename):
            return default_data
            
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content or content == "{}":
                    return default_data
                data = json.loads(content)
                
                # Ensure all categories exist in the loaded data
                for cat in self.categories:
                    if cat not in data:
                        data[cat] = []
                return data
        except json.JSONDecodeError:
            return default_data

    def save_data(self):
        """Writes current data to json."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save data: {e}")

    def setup_ui(self):
        # Central Widget & Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 0. Top Bar (Toggle)
        top_bar = QHBoxLayout()
        self.definitions_toggle = QCheckBox("Show Definitions")
        self.definitions_toggle.setChecked(True)
        self.definitions_toggle.toggled.connect(self.toggle_definitions)
        
        # Changed text to white and added a dark background to make it visible
        self.definitions_toggle.setStyleSheet("""
            font-weight: bold; 
            color: white; 
            background-color: #333; 
            padding: 4px; 
            border-radius: 5px;
        """)
        
        top_bar.addStretch() # Push subsequent widgets to the right
        top_bar.addWidget(self.definitions_toggle)
        main_layout.addLayout(top_bar)
        
        # 1. Tabs Area
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        for category in self.categories:
            # Create a tab widget
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            
            # Create table for this tab
            table = QTableWidget()
            table.setColumnCount(3) # Added 3rd column for delete button
            table.setHorizontalHeaderLabels(["Russian", "English Definition", ""])
            
            # Style the header
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Fixed) # Fixed size for button column
            table.setColumnWidth(2, 60) # Slightly wider to accommodate the centered button nicely
            
            # Store table reference and populate
            self.tables[category] = table
            self.refresh_table(category)
            
            tab_layout.addWidget(table)
            self.tabs.addTab(tab, category.title())

        # 2. Input Area (Bottom)
        # Using Grid Layout to place keyboard under the russian input
        input_grid = QGridLayout()
        
        self.russian_input = QLineEdit()
        self.russian_input.setPlaceholderText("Enter Russian word/phrase...")
        
        self.english_input = QLineEdit()
        self.english_input.setPlaceholderText("Enter English definition...")
        
        self.add_button = QPushButton("Add")
        self.add_button.setMinimumHeight(40)
        self.add_button.clicked.connect(self.add_entry)
        
        # Add widgets to grid
        # Row 0: Russian Input | English Input | Add Button
        input_grid.addWidget(self.russian_input, 0, 0)
        input_grid.addWidget(self.english_input, 0, 1)
        input_grid.addWidget(self.add_button, 0, 2)
        
        # Row 1, Col 0: Keyboard (under Russian input)
        keyboard_widget = self.create_keyboard()
        # AlignTop ensures it doesn't spread vertically if the row is tall
        input_grid.addWidget(keyboard_widget, 1, 0, alignment=Qt.AlignTop | Qt.AlignLeft)
        
        # Row 1, Col 1: Stats & Practice Panel (under English input)
        self.stats_container = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_container)
        self.stats_layout.setContentsMargins(10, 10, 0, 0)
        
        # --- Stats ---
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #555; font-size: 16px;")
        self.stats_layout.addWidget(self.stats_label)
        
        self.stats_layout.addSpacing(20) # Space between stats and practice
        
        # --- Practice Controls ---
        practice_label = QLabel("Practice Flashcards:")
        practice_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.stats_layout.addWidget(practice_label)
        
        practice_row = QHBoxLayout()
        
        self.card_count_spin = QSpinBox()
        self.card_count_spin.setRange(1, 100)
        self.card_count_spin.setValue(10)
        self.card_count_spin.setFixedWidth(70) # Fixed width for number only
        self.card_count_spin.setMinimumHeight(30)
        
        practice_btn = QPushButton("Start")
        practice_btn.setMinimumHeight(30)
        practice_btn.clicked.connect(self.start_practice)
        
        practice_row.addWidget(self.card_count_spin)
        practice_row.addWidget(practice_btn)
        
        self.stats_layout.addLayout(practice_row)
        
        # Add stretch to push everything to the top
        self.stats_layout.addStretch()
        
        input_grid.addWidget(self.stats_container, 1, 1, alignment=Qt.AlignTop)

        # Update stats initially
        self.update_stats()
        
        # Adjust column stretch to make text boxes expand, but button stay small
        input_grid.setColumnStretch(0, 1)
        input_grid.setColumnStretch(1, 1)
        input_grid.setColumnStretch(2, 0)
        
        main_layout.addLayout(input_grid)

    def start_practice(self):
        """Starts the flashcard practice dialog."""
        current_index = self.tabs.currentIndex()
        current_category = self.categories[current_index]
        items = self.data[current_category]
        
        if not items:
            QMessageBox.information(self, "No Items", f"No items in '{current_category}' to practice!")
            return
            
        # Select random items
        count = self.card_count_spin.value()
        # If requested count is more than available, just take all available
        sample_size = min(count, len(items))
        
        selected_items = random.sample(items, sample_size)
        
        # Launch Dialog
        dialog = FlashcardDialog(selected_items, self)
        dialog.exec()

    def toggle_definitions(self, checked):
        """Toggles the visibility of the English Definition column in all tables."""
        for table in self.tables.values():
            # Column 1 is English Definition
            table.setColumnHidden(1, not checked)

    def create_keyboard(self):
        """Creates a widget containing a standard Russian keyboard layout."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(2)
        
        self.letter_buttons = [] # Reset list

        # Helper to create a row of keys
        def create_key_row(keys, left_padding=0):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)
            if left_padding > 0:
                row_layout.addSpacing(left_padding) # Stagger effect
                
            for key in keys:
                btn = QPushButton(key)
                btn.setFixedSize(30, 30)
                btn.setFocusPolicy(Qt.NoFocus)
                # Capture the specific character for this button
                btn.clicked.connect(lambda checked=False, k=key: self.insert_char(k))
                row_layout.addWidget(btn)
                
                # Only track letters for shifting
                if key.isalpha():
                    self.letter_buttons.append(btn)
            
            row_layout.addStretch()
            return row_layout

        # Row 0: ё (New top row) - 10px indent to match Row 1
        layout.addLayout(create_key_row(["ё"], left_padding=10))

        # Row 1: Main top row - 10px indent
        layout.addLayout(create_key_row("й ц у к е н г ш щ з х ъ".split(), left_padding=10))

        # Row 2 (Staggered) - 30px indent (20px shift from Row 1)
        layout.addLayout(create_key_row("ф ы в а п р о л д ж э".split(), left_padding=30))

        # Row 3 (Shift + Keys + Punctuation)
        # Shift button is 50px wide, so letter keys start at ~52px
        # This creates a ~20px step from Row 2 (30px) -> Row 3 (50px)
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(2)
        
        # Shift Button
        self.shift_btn = QPushButton("↑")
        self.shift_btn.setFixedSize(50, 30) # Wider than letter keys
        self.shift_btn.setCheckable(True)
        self.shift_btn.setFocusPolicy(Qt.NoFocus)
        self.shift_btn.clicked.connect(self.toggle_shift)
        row3_layout.addWidget(self.shift_btn)
        
        # Remaining letters
        row3_keys = "я ч с м и т ь б ю".split()
        for key in row3_keys:
            btn = QPushButton(key)
            btn.setFixedSize(30, 30)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda checked=False, k=key: self.insert_char(k))
            row3_layout.addWidget(btn)
            self.letter_buttons.append(btn)
            
        # Punctuation keys (added to the right)
        punctuation = [",", ".", "!", "?"]
        for punct in punctuation:
            btn = QPushButton(punct)
            btn.setFixedSize(30, 30)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda checked=False, k=punct: self.insert_char(k))
            row3_layout.addWidget(btn)
            # Note: We do NOT add punctuation to self.letter_buttons so they aren't affected by shift
            
        row3_layout.addStretch()
        layout.addLayout(row3_layout)
        
        # Row 4 (Spacebar)
        row4_layout = QHBoxLayout()
        space_btn = QPushButton("Space")
        space_btn.setFixedHeight(30)
        space_btn.setFocusPolicy(Qt.NoFocus)
        # Expanding policy ensures it spans the available width
        space_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        space_btn.clicked.connect(lambda: self.insert_char(" "))
        
        row4_layout.addWidget(space_btn)
        layout.addLayout(row4_layout)
        
        # Push everything to the top
        layout.addStretch()
            
        return container

    def update_stats(self):
        """Updates the statistics label with current counts."""
        parts = []
        for category in self.categories:
            count = len(self.data[category])
            # Format: "all words" -> "Words"
            display_name = category.replace("all ", "").title()
            parts.append(f"{display_name}: {count}")
        
        # Join with a separator
        self.stats_label.setText("   |   ".join(parts))

    def toggle_shift(self, checked):
        """Toggles shift state and updates button labels."""
        self.is_shifted = checked
        
        # Update text on all letter buttons
        for btn in self.letter_buttons:
            current_text = btn.text()
            if self.is_shifted:
                btn.setText(current_text.upper())
            else:
                btn.setText(current_text.lower())

    def insert_char(self, char):
        """Inserts a character into the russian input field at current cursor position."""
        if char == " ":
            self.russian_input.insert(" ")
            return

        # Handle capitalization only for letters
        if char.isalpha():
            to_insert = char.upper() if self.is_shifted else char.lower()
        else:
            to_insert = char
            
        self.russian_input.insert(to_insert)
        
        # Auto-unshift after typing one character (like mobile keyboards)
        if self.is_shifted:
            self.shift_btn.setChecked(False)
            self.toggle_shift(False)

    def refresh_table(self, category):
        """Clears and rebuilds the table for a specific category."""
        table = self.tables[category]
        items = self.data[category]
        
        table.setRowCount(0) # Clear existing rows
        
        for row_idx, item in enumerate(items):
            table.insertRow(row_idx)
            
            # Text Items
            russian_item = QTableWidgetItem(item.get("russian", ""))
            english_item = QTableWidgetItem(item.get("english", ""))
            
            table.setItem(row_idx, 0, russian_item)
            table.setItem(row_idx, 1, english_item)
            
            # Delete Button Container
            # We use a container widget with a layout to perfectly center the button
            container_widget = QWidget()
            layout = QHBoxLayout(container_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            
            # Delete Button
            delete_btn = QPushButton("✕") # Using a nicer unicode X
            delete_btn.setFixedSize(30, 30)
            
            # Styling: Transparent background (matches box), no border, larger red font
            delete_btn.setStyleSheet("""
                QPushButton {
                    color: #d32f2f;
                    font-weight: bold;
                    font-size: 18px;
                    border: none;
                    background-color: transparent;
                }
                QPushButton:hover {
                    color: red;
                    font-weight: 900;
                }
            """)
            
            # Connect functionality
            delete_btn.clicked.connect(lambda checked=False, c=category, r=row_idx: self.delete_entry(c, r))
            
            layout.addWidget(delete_btn)
            table.setCellWidget(row_idx, 2, container_widget)

    def delete_entry(self, category, row_index):
        """Removes an entry by index and refreshes."""
        if 0 <= row_index < len(self.data[category]):
            self.data[category].pop(row_index)
            self.save_data()
            self.refresh_table(category)
            self.update_stats() # Update stats on delete

    def add_entry(self):
        """Adds the input text to the currently selected tab's list."""
        russian_text = self.russian_input.text().strip()
        english_text = self.english_input.text().strip()
        
        if not russian_text or not english_text:
            QMessageBox.warning(self, "Missing Info", "Please fill in both Russian and English fields.")
            return

        # Determine which tab is active
        current_index = self.tabs.currentIndex()
        current_category = self.categories[current_index]
        
        # Update data
        new_entry = {"russian": russian_text, "english": english_text}
        self.data[current_category].append(new_entry)
        
        # Save and Refresh
        self.save_data()
        self.refresh_table(current_category)
        self.update_stats() # Update stats on add
        
        # Clear inputs and refocus
        self.russian_input.clear()
        self.english_input.clear()
        self.russian_input.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = VocabVault()
    window.show()
    sys.exit(app.exec())