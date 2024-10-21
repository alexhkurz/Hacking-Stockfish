import sys
import chess
import chess.svg
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit, QListWidget, QListWidgetItem
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QSize
from analyze import ChessAnalyzer 
import io




class ChessAnalyzerGUI(QMainWindow):
    def __init__(self, analyzer):
        super().__init__()
        self.analyzer = analyzer
        self.current_position = 0
        self.analysis = None
        self.critical_moments = None
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Chess Game Analyzer')
        self.setMinimumSize(1000, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.board_widget = QSvgWidget()
        self.board_widget.setFixedSize(400, 400)
        left_layout.addWidget(self.board_widget)
        
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton('Previous')
        self.next_button = QPushButton('Next')
        self.prev_button.clicked.connect(self.prev_move)
        self.next_button.clicked.connect(self.next_move)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        left_layout.addLayout(nav_layout)
        
        layout.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.move_label = QLabel('Move: ')
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        
        right_layout.addWidget(self.move_label)
        right_layout.addWidget(QLabel('Top Sequences:'))
        right_layout.addWidget(self.analysis_text)
        
        # Add Critical Moments List
        self.critical_moments_list = QListWidget()
        self.critical_moments_list.itemClicked.connect(self.critical_moment_clicked)
        right_layout.addWidget(QLabel('Critical Moments:'))
        right_layout.addWidget(self.critical_moments_list)
        
        layout.addWidget(right_panel)
        
        pgn_input = QTextEdit()
        pgn_input.setPlaceholderText("Enter PGN here...")
        analyze_button = QPushButton('Analyze')
        analyze_button.clicked.connect(lambda: self.analyze_pgn(pgn_input.toPlainText()))
        
        input_layout = QVBoxLayout()
        input_layout.addWidget(pgn_input)
        input_layout.addWidget(analyze_button)
        
        layout.addLayout(input_layout)
    
    def analyze_pgn(self, pgn_string):
        self.analysis, self.critical_moments = self.analyzer.analyzeGame(pgn_string)
        self.current_position = 0
        self.update_display()
        self.update_critical_moments_list()
    
    def update_display(self):
        if not self.analysis:
            return
        
        pos = self.analysis[self.current_position]
        
        board = chess.Board(pos['fen'])
        self.board_widget.load(chess.svg.board(board).encode())
        
        move, move_count = pos['move']
        move_number = (move_count // 2) + 1  # Calculate the move number
        color = "White" if move_count % 2 == 0 else "Black"
        self.move_label.setText(f"Move {move_number} ({color}): {move}")
        
        analysis_text = "Top Sequences:\n"
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
