import sys
import json
import os
import random
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTabWidget, QLineEdit, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QMessageBox, QGridLayout, QSizePolicy, QLabel,
                               QCheckBox, QSpinBox, QDialog, QFrame, QScrollArea)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt, QTimer

# --- FLASHCARD DIALOG ---
class FlashcardDialog(QDialog):
    def __init__(self, items, max_score=10, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Practice Mode")
        self.resize(400, 300)
        
        self.items = items
        self.max_score = max_score
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
        
        # --- BUTTONS AREA ---
        self.button_layout = QHBoxLayout()
        
        # 1. "I Know This" Button (Green)
        self.btn_know = QPushButton("I Know This (+1)")
        self.btn_know.setMinimumHeight(50)
        self.btn_know.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; font-size: 16px;")
        self.btn_know.clicked.connect(self.mark_known)
        
        # 2. "I Don't Know" Button (Red)
        self.btn_dont_know = QPushButton("I Don't Know (-1)")
        self.btn_dont_know.setMinimumHeight(50)
        self.btn_dont_know.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; font-size: 16px;")
        self.btn_dont_know.clicked.connect(self.mark_unknown)
        
        # 3. "Next" Button (Neutral - initially hidden)
        self.btn_next = QPushButton("Next Card")
        self.btn_next.setMinimumHeight(50)
        self.btn_next.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.btn_next.clicked.connect(self.next_card)
        self.btn_next.hide()

        self.button_layout.addWidget(self.btn_dont_know)
        self.button_layout.addWidget(self.btn_know)
        self.button_layout.addWidget(self.btn_next)
        
        self.layout.addLayout(self.button_layout)
        
        self.show_card()

    def show_card(self):
        """Display the current card and reset buttons."""
        item = self.items[self.current_index]
        self.russian_label.setText(item['russian'])
        self.english_label.setText(item['english'])
        
        # Hide answer initially
        self.english_label.hide()
        
        # Show Choice buttons, Hide Next button
        self.btn_know.show()
        self.btn_dont_know.show()
        self.btn_next.hide()
        
        self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.items)}")

    def mark_known(self):
        """User guessed right. Add 1, CAP at max_score."""
        item = self.items[self.current_index]
        current_score = item.get('score', 0)
        item['score'] = min(current_score + 1, self.max_score)
        self.reveal_answer()

    def mark_unknown(self):
        """User guessed wrong. Subtract 1, NO FLOOR."""
        item = self.items[self.current_index]
        current_score = item.get('score', 0)
        item['score'] = current_score - 1
        self.reveal_answer()

    def reveal_answer(self):
        """Shows the answer and switches to Next button."""
        self.english_label.show()
        
        # Hide choices, show Next
        self.btn_know.hide()
        self.btn_dont_know.hide()
        self.btn_next.show()
        
        # Update text if it's the last card
        if self.current_index == len(self.items) - 1:
            self.btn_next.setText("Finish Practice")

    def next_card(self):
        """Move to next index or close."""
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self.show_card()
        else:
            self.accept() # Close dialog

# --- MATCHING DIALOG ---
class MatchingDialog(QDialog):
    def __init__(self, items, max_score=10, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Matching Exercise")
        self.resize(600, 600) 
        
        # We process items in chunks of 10
        self.all_items = items
        self.max_score = max_score
        self.round_size = 10
        self.current_round = 0
        self.total_rounds = (len(items) + self.round_size - 1) // self.round_size
        
        self.selected_russian = None 
        self.selected_english = None 
        
        # UI Setup
        self.layout = QVBoxLayout(self)
        
        # Header
        self.header_label = QLabel()
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ddd;")
        self.layout.addWidget(self.header_label)
        
        # Game Area
        self.game_area = QWidget()
        self.grid = QGridLayout(self.game_area)
        self.layout.addWidget(self.game_area)
        
        # Status/Result message
        self.status_label = QLabel("Select a pair to match.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; color: #aaa; margin-top: 10px;")
        self.layout.addWidget(self.status_label)

        # Next Round / Finish Button
        self.action_btn = QPushButton("Next Round")
        self.action_btn.setMinimumHeight(40)
        self.action_btn.clicked.connect(self.next_round)
        self.action_btn.hide()
        self.layout.addWidget(self.action_btn)
        
        self.start_round()

    def start_round(self):
        """Prepares the grid for the current chunk of words."""
        self.action_btn.hide()
        self.status_label.setText("Select a Russian word and its English definition.")
        
        # Clear grid
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
            
        # Get chunk
        start = self.current_round * self.round_size
        end = start + self.round_size
        current_items = self.all_items[start:end]
        
        self.header_label.setText(f"Round {self.current_round + 1} of {self.total_rounds}")
        
        # Create lists for columns
        russian_btns = []
        english_btns = []
        
        for item in current_items:
            # Russian Button
            r_btn = QPushButton(item['russian'])
            r_btn.setMinimumHeight(50)
            r_btn.setCheckable(True)
            r_btn.setStyleSheet(self.get_btn_style("neutral"))
            r_btn.item_data = item 
            r_btn.type = "russian"
            r_btn.clicked.connect(lambda checked=False, b=r_btn: self.handle_click(b))
            russian_btns.append(r_btn)
            
            # English Button
            e_btn = QPushButton(item['english'])
            e_btn.setMinimumHeight(50)
            e_btn.setCheckable(True)
            e_btn.setStyleSheet(self.get_btn_style("neutral"))
            e_btn.item_data = item
            e_btn.type = "english"
            e_btn.clicked.connect(lambda checked=False, b=e_btn: self.handle_click(b))
            english_btns.append(e_btn)
            
        # Shuffle English buttons so they don't align perfectly
        random.shuffle(english_btns)
        
        # Add to Grid (Left: Russian, Right: English)
        for i, r_btn in enumerate(russian_btns):
            self.grid.addWidget(r_btn, i, 0)
            
        for i, e_btn in enumerate(english_btns):
            self.grid.addWidget(e_btn, i, 1)
            
        self.remaining_pairs = len(current_items)

    def handle_click(self, btn):
        if (btn == self.selected_russian) or (btn == self.selected_english):
            btn.setChecked(False)
            btn.setStyleSheet(self.get_btn_style("neutral"))
            if btn.type == "russian": self.selected_russian = None
            else: self.selected_english = None
            return

        # Handle Selection
        if btn.type == "russian":
            if self.selected_russian:
                self.selected_russian.setChecked(False)
                self.selected_russian.setStyleSheet(self.get_btn_style("neutral"))
            self.selected_russian = btn
            btn.setStyleSheet(self.get_btn_style("selected"))
            
        elif btn.type == "english":
            if self.selected_english:
                self.selected_english.setChecked(False)
                self.selected_english.setStyleSheet(self.get_btn_style("neutral"))
            self.selected_english = btn
            btn.setStyleSheet(self.get_btn_style("selected"))

        if self.selected_russian and self.selected_english:
            self.validate_match()

    def validate_match(self):
        r_item = self.selected_russian.item_data
        e_item = self.selected_english.item_data
        
        is_match = (r_item == e_item)
        
        if is_match:
            self.selected_russian.setStyleSheet(self.get_btn_style("correct"))
            self.selected_english.setStyleSheet(self.get_btn_style("correct"))
            self.selected_russian.setEnabled(False)
            self.selected_english.setEnabled(False)
            
            # Score +1
            current = r_item.get('score', 0)
            r_item['score'] = min(current + 1, self.max_score)
            
            self.selected_russian = None
            self.selected_english = None
            self.remaining_pairs -= 1
            
            if self.remaining_pairs == 0:
                self.finish_round()
                
        else:
            self.status_label.setText("Incorrect match! Try again.")
            self.status_label.setStyleSheet("font-size: 16px; color: #ff5555; font-weight: bold;")
            
            self.selected_russian.setStyleSheet(self.get_btn_style("wrong"))
            self.selected_english.setStyleSheet(self.get_btn_style("wrong"))
            
            # Score -1
            r_item['score'] = r_item.get('score', 0) - 1
            e_item['score'] = e_item.get('score', 0) - 1

            QApplication.processEvents() 
            
            self.selected_russian.setChecked(False)
            self.selected_english.setChecked(False)
            
            QTimer.singleShot(500, lambda: self.reset_wrong_buttons(self.selected_russian, self.selected_english))
            
            self.selected_russian = None
            self.selected_english = None

    def reset_wrong_buttons(self, btn1, btn2):
        try:
            if btn1: btn1.setStyleSheet(self.get_btn_style("neutral"))
            if btn2: btn2.setStyleSheet(self.get_btn_style("neutral"))
        except:
            pass

    def finish_round(self):
        self.status_label.setText("Round Complete!")
        self.status_label.setStyleSheet("font-size: 18px; color: #55ff55; font-weight: bold;")
        
        if self.current_round < self.total_rounds - 1:
            self.action_btn.setText("Start Next Round")
            self.action_btn.show()
        else:
            self.action_btn.setText("Finish Exercise")
            self.action_btn.show()

    def next_round(self):
        if self.current_round < self.total_rounds - 1:
            self.current_round += 1
            self.start_round()
        else:
            self.accept()

    def get_btn_style(self, state):
        # UPDATED: Increased font-size to 20px
        base = """
            QPushButton { border-radius: 8px; font-size: 20px; font-weight: bold; padding: 5px; border: 2px solid #555; }
        """
        if state == "neutral":
            return base + "QPushButton { background-color: #333; font-weight: normal; color: white; } QPushButton:hover { background-color: #444; }"
        elif state == "selected":
            return base + "QPushButton { background-color: #fbc02d; color: black; border: 2px solid #ffeb3b; }"
        elif state == "correct":
            return base + "QPushButton { background-color: #2e7d32; color: white; border: 2px solid #4caf50; }"
        elif state == "wrong":
            return base + "QPushButton { background-color: #c62828; color: white; border: 2px solid #ff5252; }"
        return base

# --- MAIN WINDOW ---
class VocabVault(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vocab Vault")
        self.resize(1280, 720)
        
        # CONFIG: Max Score Cap
        self.MAX_SCORE = 10

        # Global font size
        font = QFont()
        font.setPointSize(14)
        self.setFont(font)
        
        self.filename = "russian.json"
        self.categories = ["all words", "all phrases", "all sentences"]
        self.tables = {} 
        self.letter_buttons = [] 
        self.is_shifted = False
        
        self.data = self.load_data()
        self.setup_ui()

    def load_data(self):
        """Loads data from json, initializes structure and ensures 'score' exists."""
        default_data = {cat: [] for cat in self.categories}
        
        if not os.path.exists(self.filename):
            return default_data
            
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content or content == "{}":
                    return default_data
                data = json.loads(content)
                
                # Sanitize data: Ensure categories exist and items have scores
                for cat in self.categories:
                    if cat not in data:
                        data[cat] = []
                    # Backfill score for existing items
                    for item in data[cat]:
                        if "score" not in item:
                            item["score"] = 0
                            
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 0. Top Bar
        top_bar = QHBoxLayout()
        self.definitions_toggle = QCheckBox("Show Definitions")
        self.definitions_toggle.setChecked(True)
        self.definitions_toggle.toggled.connect(self.toggle_definitions)
        self.definitions_toggle.setStyleSheet("""
            font-weight: bold; color: white; background-color: #333; 
            padding: 4px; border-radius: 5px;
        """)
        top_bar.addStretch()
        top_bar.addWidget(self.definitions_toggle)
        main_layout.addLayout(top_bar)
        
        # 1. Tabs Area
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        for category in self.categories:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            
            table = QTableWidget()
            table.setColumnCount(4) 
            table.setHorizontalHeaderLabels(["Russian", "English Definition", "Score", ""])
            
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Fixed) # Score width
            table.setColumnWidth(2, 80)
            header.setSectionResizeMode(3, QHeaderView.Fixed) # Button width
            table.setColumnWidth(3, 60)
            
            self.tables[category] = table
            self.refresh_table(category)
            
            tab_layout.addWidget(table)
            self.tabs.addTab(tab, category.title())

        # 2. Input Area
        input_grid = QGridLayout()
        
        self.russian_input = QLineEdit()
        self.russian_input.setPlaceholderText("Enter Russian word/phrase...")
        
        self.english_input = QLineEdit()
        self.english_input.setPlaceholderText("Enter English definition...")
        
        self.add_button = QPushButton("Add")
        self.add_button.setMinimumHeight(40)
        self.add_button.clicked.connect(self.add_entry)
        
        input_grid.addWidget(self.russian_input, 0, 0)
        input_grid.addWidget(self.english_input, 0, 1)
        input_grid.addWidget(self.add_button, 0, 2)
        
        keyboard_widget = self.create_keyboard()
        input_grid.addWidget(keyboard_widget, 1, 0, alignment=Qt.AlignTop | Qt.AlignLeft)
        
        # Stats & Practice Container
        self.stats_container = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_container)
        self.stats_layout.setContentsMargins(10, 10, 0, 0)
        
        # Stats Label
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #555; font-size: 16px;")
        self.stats_label.setWordWrap(True)
        self.stats_layout.addWidget(self.stats_label)
        
        self.stats_layout.addSpacing(20)
        
        # --- FLASHCARD PRACTICE ROW ---
        flashcard_label = QLabel("Practice Flashcards:")
        flashcard_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.stats_layout.addWidget(flashcard_label)
        
        fc_row = QHBoxLayout()
        self.card_count_spin = QSpinBox()
        self.card_count_spin.setRange(1, 100)
        self.card_count_spin.setValue(10)
        self.card_count_spin.setFixedWidth(60)
        self.card_count_spin.setMinimumHeight(35)
        
        self.btn_fc_random = QPushButton("Random")
        self.btn_fc_random.setMinimumHeight(35)
        self.btn_fc_random.clicked.connect(lambda: self.start_practice(mode="random"))

        self.btn_fc_weak = QPushButton("Weak")
        self.btn_fc_weak.setMinimumHeight(35)
        self.btn_fc_weak.clicked.connect(lambda: self.start_practice(mode="weak"))

        fc_row.addWidget(self.card_count_spin)
        fc_row.addWidget(self.btn_fc_random)
        fc_row.addWidget(self.btn_fc_weak)
        self.stats_layout.addLayout(fc_row)

        self.stats_layout.addSpacing(10)

        # --- MATCHING GAME ROW ---
        matching_label = QLabel("Matching Exercise (10 pairs/card):")
        matching_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.stats_layout.addWidget(matching_label)

        match_row = QHBoxLayout()
        self.match_count_spin = QSpinBox()
        self.match_count_spin.setRange(1, 10) # 1 to 10 rounds (10 to 100 words)
        self.match_count_spin.setValue(1) # Default 1 round
        self.match_count_spin.setFixedWidth(60)
        self.match_count_spin.setMinimumHeight(35)

        self.btn_match_random = QPushButton("Random")
        self.btn_match_random.setMinimumHeight(35)
        self.btn_match_random.clicked.connect(lambda: self.start_matching(mode="random"))

        self.btn_match_weak = QPushButton("Weak")
        self.btn_match_weak.setMinimumHeight(35)
        self.btn_match_weak.clicked.connect(lambda: self.start_matching(mode="weak"))

        match_row.addWidget(self.match_count_spin)
        match_row.addWidget(self.btn_match_random)
        match_row.addWidget(self.btn_match_weak)
        self.stats_layout.addLayout(match_row)
        
        self.stats_layout.addStretch()
        
        input_grid.addWidget(self.stats_container, 1, 1, alignment=Qt.AlignTop)
        self.update_stats()
        
        input_grid.setColumnStretch(0, 1)
        input_grid.setColumnStretch(1, 1)
        input_grid.setColumnStretch(2, 0)
        
        main_layout.addLayout(input_grid)

    def start_practice(self, mode="random"):
        current_index = self.tabs.currentIndex()
        current_category = self.categories[current_index]
        items = self.data[current_category]
        
        if not items:
            QMessageBox.information(self, "No Items", f"No items in '{current_category}' to practice!")
            return
            
        count = self.card_count_spin.value()
        
        if mode == "weak":
            sorted_items = sorted(items, key=lambda x: x.get('score', 0))
            selected_items = sorted_items[:count]
            random.shuffle(selected_items)
        else:
            sample_size = min(count, len(items))
            selected_items = random.sample(items, sample_size)
            
        dialog = FlashcardDialog(selected_items, max_score=self.MAX_SCORE, parent=self)
        dialog.exec()
        
        self.save_data()
        self.refresh_table(current_category)
        self.update_stats()

    def start_matching(self, mode="random"):
        current_index = self.tabs.currentIndex()
        current_category = self.categories[current_index]
        items = self.data[current_category]
        
        if not items:
            QMessageBox.information(self, "No Items", f"No items in '{current_category}' to practice!")
            return
        
        rounds = self.match_count_spin.value()
        total_items_needed = rounds * 10
        
        # Cap at available items
        count = min(total_items_needed, len(items))
        
        if count == 0:
            return

        if mode == "weak":
            sorted_items = sorted(items, key=lambda x: x.get('score', 0))
            selected_items = sorted_items[:count]
            random.shuffle(selected_items)
        else:
            selected_items = random.sample(items, count)

        dialog = MatchingDialog(selected_items, max_score=self.MAX_SCORE, parent=self)
        dialog.exec()
        
        self.save_data()
        self.refresh_table(current_category)
        self.update_stats()

    def toggle_definitions(self, checked):
        for table in self.tables.values():
            table.setColumnHidden(1, not checked)

    def create_keyboard(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(2)
        self.letter_buttons = []

        def create_key_row(keys, left_padding=0):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)
            if left_padding > 0:
                row_layout.addSpacing(left_padding)
            for key in keys:
                btn = QPushButton(key)
                btn.setFixedSize(30, 30)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.clicked.connect(lambda checked=False, k=key: self.insert_char(k))
                row_layout.addWidget(btn)
                if key.isalpha():
                    self.letter_buttons.append(btn)
            row_layout.addStretch()
            return row_layout

        layout.addLayout(create_key_row(["ё"], left_padding=10))
        layout.addLayout(create_key_row("й ц у к е н г ш щ з х ъ".split(), left_padding=10))
        layout.addLayout(create_key_row("ф ы в а п р о л д ж э".split(), left_padding=30))

        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(2)
        self.shift_btn = QPushButton("↑")
        self.shift_btn.setFixedSize(50, 30)
        self.shift_btn.setCheckable(True)
        self.shift_btn.setFocusPolicy(Qt.NoFocus)
        self.shift_btn.clicked.connect(self.toggle_shift)
        row3_layout.addWidget(self.shift_btn)
        
        for key in "я ч с м и т ь б ю".split():
            btn = QPushButton(key)
            btn.setFixedSize(30, 30)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda checked=False, k=key: self.insert_char(k))
            row3_layout.addWidget(btn)
            self.letter_buttons.append(btn)
        
        for punct in [",", ".", "!", "?"]:
            btn = QPushButton(punct)
            btn.setFixedSize(30, 30)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda checked=False, k=punct: self.insert_char(k))
            row3_layout.addWidget(btn)
            
        row3_layout.addStretch()
        layout.addLayout(row3_layout)
        
        row4_layout = QHBoxLayout()
        space_btn = QPushButton("Space")
        space_btn.setFixedHeight(30)
        space_btn.setFocusPolicy(Qt.NoFocus)
        space_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        space_btn.clicked.connect(lambda: self.insert_char(" "))
        row4_layout.addWidget(space_btn)
        layout.addLayout(row4_layout)
        layout.addStretch()
        return container

    def update_stats(self):
        parts = []
        total_items_count = 0
        
        for category in self.categories:
            count = len(self.data[category])
            total_items_count += count
            display_name = category.replace("all ", "").title()
            parts.append(f"{display_name}: {count}")
        
        current_total_score = 0
        for category in self.categories:
            for item in self.data[category]:
                current_total_score += item.get('score', 0)
        
        max_possible_score = total_items_count * self.MAX_SCORE
        
        score_color = "green" if current_total_score >= 0 else "red"
        
        stats_text = "   |   ".join(parts)
        final_text = (f"{stats_text}<br><br>"
                      f"<b>Total Mastery Score: <span style='color:{score_color};'>{current_total_score}</span> / {max_possible_score}</b>")
        
        self.stats_label.setText(final_text)

    def toggle_shift(self, checked):
        self.is_shifted = checked
        for btn in self.letter_buttons:
            current_text = btn.text()
            if self.is_shifted:
                btn.setText(current_text.upper())
            else:
                btn.setText(current_text.lower())

    def insert_char(self, char):
        if char == " ":
            self.russian_input.insert(" ")
            return
        if char.isalpha():
            to_insert = char.upper() if self.is_shifted else char.lower()
        else:
            to_insert = char
        self.russian_input.insert(to_insert)
        if self.is_shifted:
            self.shift_btn.setChecked(False)
            self.toggle_shift(False)

    def refresh_table(self, category):
        table = self.tables[category]
        items = self.data[category]
        table.setRowCount(0)
        
        for row_idx, item in enumerate(items):
            table.insertRow(row_idx)
            
            table.setItem(row_idx, 0, QTableWidgetItem(item.get("russian", "")))
            table.setItem(row_idx, 1, QTableWidgetItem(item.get("english", "")))
            
            score = item.get("score", 0)
            score_item = QTableWidgetItem(str(score))
            score_item.setTextAlignment(Qt.AlignCenter)
            
            if score > 0:
                score_item.setForeground(QColor("green"))
            elif score < 0:
                score_item.setForeground(QColor("red"))
                
            table.setItem(row_idx, 2, score_item)
            
            container_widget = QWidget()
            layout = QHBoxLayout(container_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            delete_btn = QPushButton("✕")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setStyleSheet("""
                QPushButton { color: #d32f2f; font-weight: bold; font-size: 18px; border: none; background: transparent; }
                QPushButton:hover { color: red; font-weight: 900; }
            """)
            delete_btn.clicked.connect(lambda checked=False, c=category, r=row_idx: self.delete_entry(c, r))
            layout.addWidget(delete_btn)
            table.setCellWidget(row_idx, 3, container_widget)

    def delete_entry(self, category, row_index):
        if 0 <= row_index < len(self.data[category]):
            self.data[category].pop(row_index)
            self.save_data()
            self.refresh_table(category)
            self.update_stats()

    def add_entry(self):
        russian_text = self.russian_input.text().strip()
        english_text = self.english_input.text().strip()
        
        if not russian_text or not english_text:
            QMessageBox.warning(self, "Missing Info", "Please fill in both Russian and English fields.")
            return

        current_index = self.tabs.currentIndex()
        current_category = self.categories[current_index]
        
        new_entry = {"russian": russian_text, "english": english_text, "score": 0}
        self.data[current_category].append(new_entry)
        
        self.save_data()
        self.refresh_table(current_category)
        self.update_stats()
        
        self.russian_input.clear()
        self.english_input.clear()
        self.russian_input.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = VocabVault()
    window.show()
    sys.exit(app.exec())