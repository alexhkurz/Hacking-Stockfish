import sys
import chess
import chess.svg
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QSize
from analyze import ChessAnalyzer 

class ChessAnalyzerGUI(QMainWindow):
    def __init__(self, analyzer):
        super().__init__()
        self.analyzer = analyzer
        self.current_position = 0
        self.analysis = None
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Chess Game Analyzer')
        self.setMinimumSize(800, 600)
        
        #Center
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        #Left side 
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.board_widget = QSvgWidget()
        self.board_widget.setFixedSize(400, 400)
        left_layout.addWidget(self.board_widget)
        
        #Navigation 
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton('Previous')
        self.next_button = QPushButton('Next')
        self.prev_button.clicked.connect(self.prev_move)
        self.next_button.clicked.connect(self.next_move)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        left_layout.addLayout(nav_layout)
        
        layout.addWidget(left_panel)
        
        #Right side
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.move_label = QLabel('Move: ')
        self.eval_label = QLabel('Evaluation: ')
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        
        right_layout.addWidget(self.move_label)
        right_layout.addWidget(self.eval_label)
        right_layout.addWidget(QLabel('Top Moves:'))
        right_layout.addWidget(self.analysis_text)
        
        layout.addWidget(right_panel)
        
        #PGN input
        pgn_input = QTextEdit()
        pgn_input.setPlaceholderText("Enter PGN here...")
        analyze_button = QPushButton('Analyze')
        analyze_button.clicked.connect(lambda: self.analyze_pgn(pgn_input.toPlainText()))
        
        input_layout = QVBoxLayout()
        input_layout.addWidget(pgn_input)
        input_layout.addWidget(analyze_button)
        
        layout.addLayout(input_layout)
    
    def analyze_pgn(self, pgn_string):
        self.analysis = self.analyzer.analyzeGame(pgn_string)
        self.current_position = 0
        self.update_display()
    
    def update_display(self):
        if not self.analysis:
            return
        
        pos = self.analysis[self.current_position]
        
        #Update board
        board = chess.Board(pos['fen'])
        self.board_widget.load(chess.svg.board(board).encode())
        #Update labels
        self.move_label.setText(f"Move: {pos['move']}")
        self.eval_label.setText(f"Evaluation: {pos['evaluation']/100}")
        #Update analysis text
        analysis_text = "Top moves:\n"
        for move, score in pos['top_moves']:
            analysis_text += f"{move} ({score})\n"
        self.analysis_text.setText(analysis_text)
    
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
    ex = ChessAnalyzerGUI(analyzer)
    ex.show()
    try:
        sys.exit(app.exec_())
    finally:
        analyzer.close()

if __name__ == '__main__':
    main()
