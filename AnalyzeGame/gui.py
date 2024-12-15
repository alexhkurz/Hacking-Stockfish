import sys
import chess
import chess.svg
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit, QListWidget, QListWidgetItem, QFileDialog, QSizePolicy
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QSize, QEvent
import os
import json
from analyze import ChessAnalyzer 
import io
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

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
        ## Chess board display
        self.board_widget = QSvgWidget()
        self.board_widget.setFixedSize(400, 400)
        left_layout.addWidget(self.board_widget)
        ## Previous/Next move buttons
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton('Previous')
        self.next_button = QPushButton('Next')
        self.prev_button.clicked.connect(self.prev_move)
        self.next_button.clicked.connect(self.next_move)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        left_layout.addLayout(nav_layout)
        ## Add left panel to layout
        layout.addWidget(left_panel)
        
        # Analysis Panel
        analysis_panel = QWidget()
        analysis_layout = QVBoxLayout(analysis_panel)  
        ## Current move display
        self.move_label = QLabel('Move: ')
        analysis_layout.addWidget(self.move_label)
        ## Create matplotlib figure for plotting scores
        self.figure = Figure(figsize=(5, 2))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMaximumHeight(200)  # Limit height of the plot
        ## Add plot to analysis layout at the top
        analysis_layout.addWidget(self.canvas)  
        ## Analysis text display
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        ## Add top sequences label and text display
        analysis_layout.addWidget(QLabel('Top Sequences:'))
        analysis_layout.addWidget(self.analysis_text)        
        ## Critical Moments List
        self.critical_moments_list = QListWidget()
        self.critical_moments_list.itemClicked.connect(self.critical_moment_clicked)
        analysis_layout.addWidget(QLabel('Critical Moments:'))
        analysis_layout.addWidget(self.critical_moments_list)        
        ## Save/Load buttons
        file_layout = QHBoxLayout()
        save_button = QPushButton('Save Analysis')
        load_button = QPushButton('Load Analysis')
        save_button.clicked.connect(self.save_analysis)
        load_button.clicked.connect(self.load_analysis)
        file_layout.addWidget(save_button)
        file_layout.addWidget(load_button)
        analysis_layout.addLayout(file_layout)
        ## Add analysis panel to layout
        layout.addWidget(analysis_panel)
        
        # Right-most Panel: PGN Input
        pgn_input = QTextEdit()
        pgn_input.setPlaceholderText("Enter PGN here...")
        pgn_input.setMaximumWidth(100)  # Set maximum width for the input

        analyze_button = QPushButton('Analyze')
        analyze_button.clicked.connect(lambda: self.analyze_pgn(pgn_input.toPlainText()))
        analyze_button.setFixedWidth(100)  # Set fixed width for the button
        analyze_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)  # Prevent horizontal expansion

        # Load and Analyze PGN from file
        load_pgn_button = QPushButton()
        load_pgn_button.clicked.connect(lambda: self.load_pgn(pgn_input))
        load_pgn_button.setFixedWidth(100)  # Set fixed width for the button        
        load_pgn_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)  # Prevent horizontal expansion
        # Create a QLabel with word wrap for the button text
        label = QLabel('Load PGN and Analyze')
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)  # Center the text
        load_pgn_button.setLayout(QVBoxLayout())
        load_pgn_button.layout().addWidget(label)
        # Set the background to white and add rounded corners
        load_pgn_button.setStyleSheet("""
            QPushButton { 
                background-color: white;
                border-radius: 5px;
            }
        """)

        input_layout = QVBoxLayout()
        input_layout.addWidget(pgn_input)
        input_layout.addWidget(analyze_button)
        input_layout.addWidget(load_pgn_button) 

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
        if not self.analysis or self.current_position >= len(self.analysis):
            return
            
        pos = self.analysis[self.current_position]
        
        # Update plot
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        scores = [score for score, _ in pos["top_sequences"]]
        moves = range(len(scores))
        ax.plot(moves, scores, 'bo-')  # Blue dots connected by lines
        # ax.set_xlabel('Move Rank')
        ax.set_ylabel('Score')
        ax.grid(True)
        ax.set_xticklabels([])  # This will remove the x-axis number labels
        self.canvas.draw()
        
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
                if event.modifiers() & Qt.ShiftModifier:  # Check if Shift is pressed
                    print("Shift+Right arrow pressed")  # Debug print
                    self.next_move()
                    self.next_move()
                else:
                    print("Right arrow pressed")  # Debug print
                    self.next_move()
                return True
            elif event.key() == Qt.Key_Left:
                if event.modifiers() & Qt.ShiftModifier:  # Check if Shift is pressed
                    print("Shift+Left arrow pressed")  # Debug print
                    self.prev_move()
                    self.prev_move()
                else:
                    print("Left arrow pressed")  # Debug print
                    self.prev_move()
                return True
            elif event.key() == Qt.Key_Up:
                print("Up arrow pressed")  # Debug print
                self.current_position = 0  # Go to start
                self.update_display()
                return True
            elif event.key() == Qt.Key_Down:
                print("Down arrow pressed")  # Debug print
                if self.analysis:
                    self.current_position = len(self.analysis) - 1  # Go to end
                    self.update_display()
                return True
        return super().eventFilter(obj, event)
    
    def save_analysis(self):
        if not self.analysis:
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Analysis",
            "GamesAnalyzed",
            "JSON Files (*.json)"
        )
        if filename:
            with open(filename, 'w') as file:
                json.dump((self.analyzer.serialize_analysis(self.analysis), self.critical_moments), file)
            
    def load_analysis(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Analysis",
            "GamesAnalyzed",
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

    def load_pgn(self, pgn_input):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load PGN",
            "",
            "PGN Files (*.pgn);;All Files (*)"
        )
        if filename:
            with open(filename, 'r') as file:
                pgn_data = file.read()
                pgn_input.setPlainText(pgn_data)
                self.analyze_pgn(pgn_data)  # Automatically analyze after loading

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

