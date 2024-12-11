import sys
import chess
import chess.svg
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit, QListWidget, QListWidgetItem, QFileDialog
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QSize, QEvent
import os
import json
from analyze import ChessAnalyzer 
import io

class ChessAnalyzerGUI(QMainWindow):
    def __init__(self, analyzer):
        super().__init__()
        self.analyzer = analyzer
        self.current_position = 0
        self.analysis = None
        self.critical_moments = None

        # Install event filter on the main window
        self.installEventFilter(self)
        # Make sure the window can accept keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)
        # Optional: Set focus when window opens
        self.setFocus()
        
        self.initUI()
        self.load_cached_analysis()
        
    def initUI(self):
        self.setWindowTitle('Chess Game Analyzer')
        self.setMinimumSize(1000, 600)
        
        # Create main central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Left Panel: Chess Board and Navigation
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        # Chess board display
        self.board_widget = QSvgWidget()
        self.board_widget.setFixedSize(400, 400)
        left_layout.addWidget(self.board_widget)
        # Previous/Next move buttons
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton('Previous')
        self.next_button = QPushButton('Next')
        self.prev_button.clicked.connect(self.prev_move)
        self.next_button.clicked.connect(self.next_move)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        left_layout.addLayout(nav_layout)
        
        layout.addWidget(left_panel)
        
        # Analysis Panel: Analysis Display
        analysis_panel = QWidget()
        analysis_layout = QVBoxLayout(analysis_panel)
        
        # Current move display
        self.move_label = QLabel('Move: ')
        
        # Analysis text display
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        
        analysis_layout.addWidget(self.move_label)
        analysis_layout.addWidget(QLabel('Top Sequences:'))
        analysis_layout.addWidget(self.analysis_text)
        
        # Critical Moments List
        self.critical_moments_list = QListWidget()
        self.critical_moments_list.itemClicked.connect(self.critical_moment_clicked)
        analysis_layout.addWidget(QLabel('Critical Moments:'))
        analysis_layout.addWidget(self.critical_moments_list)
        
        # Save/Load buttons
        file_layout = QHBoxLayout()
        save_button = QPushButton('Save Analysis')
        load_button = QPushButton('Load Analysis')
        save_button.clicked.connect(self.save_analysis)
        load_button.clicked.connect(self.load_analysis)
        file_layout.addWidget(save_button)
        file_layout.addWidget(load_button)
        analysis_layout.addLayout(file_layout)
        
        layout.addWidget(analysis_panel)
        
        # Right-most Panel: PGN Input
        pgn_input = QTextEdit()
        pgn_input.setPlaceholderText("Enter PGN here...")
        analyze_button = QPushButton('Analyze')
        analyze_button.clicked.connect(lambda: self.analyze_pgn(pgn_input.toPlainText()))
        
        input_layout = QVBoxLayout()
        input_layout.addWidget(pgn_input)
        input_layout.addWidget(analyze_button)
        
        layout.addLayout(input_layout)

    def analyze_pgn(self, pgn_string):
        print("Starting analysis...")  # Debug print
        if not pgn_string.strip():  # Check if input is empty
            print("No PGN provided")
            return
        print(f"Analyzing PGN: {pgn_string}")  # Debug print
        try:
            # Delete cache file if it exists
            if os.path.exists('analysis_cache.json'):
                os.remove('analysis_cache.json')
                
            self.analysis, self.critical_moments = self.analyzer.analyzeGame(pgn_string)
            print(f"Analysis complete. Moves analyzed: {len(self.analysis) if self.analysis else 0}")  # Debug print
            self.current_position = 0
            self.update_display()
            self.update_critical_moments_list()
        except Exception as e:
            print(f"Error during analysis: {str(e)}")  # Debug print for errors

    def load_cached_analysis(self):
        cache_file = 'analysis_cache.json'
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as file:
                    serialized_analysis, self.critical_moments = json.load(file)
                    self.analysis = self.analyzer.deserialize_analysis(serialized_analysis)
                print("Loaded analysis from cache.")
                self.current_position = 0
                self.update_display()
                self.update_critical_moments_list()
            except json.JSONDecodeError:
                print(f"Warning: Cache file {cache_file} is corrupted. Recomputing analysis.")
                os.remove(cache_file)
    
    def update_display(self):
        if not self.analysis:
            return
        
        if self.current_position >= len(self.analysis):
            self.current_position = len(self.analysis) - 1

        pos = self.analysis[self.current_position]
        
        board = chess.Board(pos['fen'])
        self.board_widget.load(chess.svg.board(board).encode())
        
        move, move_count = pos['move']
        move_number = (move_count // 2) + 1  # Calculate the move number
        color = "White" if move_count % 2 == 0 else "Black"
        self.move_label.setText(f"Move {move_number} ({color}): {move}")
        
        analysis_text = ""
        if 'a_score' in pos:
            analysis_text = f"A-score: {pos['a_score']:.2f}\n"
            if 'b_score' in pos and pos['b_score'] is not None:
                analysis_text += f"B-score: {pos['b_score']:.2f}\n"
        
        analysis_text += "\n"
        
        analysis_text += "Top Sequences:\n"
        for score, sequence in pos['top_sequences']:
            analysis_text += f"Score: {score}\n"
            analysis_text += " ".join(map(str, sequence))
            analysis_text += "\n\n"
        
        forcing_moves, forcing_count = pos['forcing_moves']
        if forcing_moves:
            analysis_text += "Forced Move:\n"
            for move in forcing_moves:
                analysis_text += f"{move}\n"
        
        self.analysis_text.setText(analysis_text.strip())
    
    def update_critical_moments_list(self):
        self.critical_moments_list.clear()
        for moment in self.critical_moments:
            item = QListWidgetItem(f"Move {moment['move_number']} ({moment['color']}): {moment['description']}")
            item.setData(Qt.UserRole, moment['move_number'] * 2 - (2 if moment['color'] == 'White' else 1))
            self.critical_moments_list.addItem(item)
    
    def critical_moment_clicked(self, item):
        self.current_position = item.data(Qt.UserRole)
        self.update_display()
    
    def next_move(self):
        if self.analysis and self.current_position < len(self.analysis) - 1:
            self.current_position += 1
            self.update_display()
    
    def prev_move(self):
        if self.analysis and self.current_position > 0:
            self.current_position -= 1
            self.update_display()
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            print(f"Key pressed: {event.key()}")  # Debug print
            if event.key() == Qt.Key_Right:
                print("Right arrow pressed")  # Debug print
                self.next_move()
                return True
            elif event.key() == Qt.Key_Left:
                print("Left arrow pressed")  # Debug print
                self.prev_move()
                return True
        return super().eventFilter(obj, event)
    
    def save_analysis(self):
        if not self.analysis:
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Analysis",
            "AnalyzedGames",
            "JSON Files (*.json)"
        )
        if filename:
            with open(filename, 'w') as file:
                json.dump((self.analyzer.serialize_analysis(self.analysis), self.critical_moments), file)
            
    def load_analysis(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Analysis",
            "AnalyzedGames",
            "JSON Files (*.json)"
        )
        if filename:
            try:
                with open(filename, 'r') as file:
                    serialized_analysis, self.critical_moments = json.load(file)
                    self.analysis = self.analyzer.deserialize_analysis(serialized_analysis)
                self.current_position = 0
                self.update_display()
                self.update_critical_moments_list()
            except json.JSONDecodeError:
                print(f"Error: File {filename} is corrupted.")

def main():
    app = QApplication(sys.argv)
    analyzer = ChessAnalyzer()
    gui = ChessAnalyzerGUI(analyzer)
    gui.show()
    try:
        sys.exit(app.exec_())
    finally:
        analyzer.close()

if __name__ == '__main__':
    main()

