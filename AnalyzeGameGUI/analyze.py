import chess
import chess.engine
import chess.pgn
import io

class ChessAnalyzer:
    def __init__(self, engine_path="/Users/kevinhuang/Documents/Projects/Hacking-Stockfish/printScores/src/stockfish"):
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    
    def analyzeGame(self, pgn_string, time_per_move=1.0):
        game = chess.pgn.read_game(io.StringIO(pgn_string))
        analysis = [] # list of dictionaries key 
        
        board = game.board()
        for move in game.mainline_moves():
            #get infoDict of current move
            info = self.engine.analyse(board, chess.engine.Limit(time=time_per_move))
            
            top_moves = []
            for i, pv in enumerate(info["pv"][:10]): 
                score = info["score"].relative.score(mate_score=10000)
                top_moves.append((pv, score))
            
            analysis.append({
                'move': board.san(move),
                'fen': board.fen(),
                'top_moves': top_moves,
                'evaluation': info["score"].relative.score(mate_score=10000)
            })
            
            board.push(move)
        
        return analysis
    
    def displayAnalysis(self, analysis):
        move_number = 1
        is_white = True
        
        for pos in analysis:
            if is_white:
                print(f"{move_number}.", end=" ")
            
            print(f"{pos['move']} ", end="")
            print(f"(Eval: {pos['evaluation']}) ", end="")
            print("Top moves:", end=" ")
            
            for move, score in pos['top_moves']:
                print(f"{move}({score})", end=" ")
            
            print()
            
            if not is_white:
                move_number += 1
            is_white = not is_white
    
    def close(self):
        self.engine.quit()

def main():
    #INPUT PGN 
    pgnString = """
    1. e4 c5 2. Nf3 a6 3. d3 g6 4. g3 Bg7 5. Bg2 b5 6. O-O Bb7 7. c3 e5 8. a3 Ne7 9. b4 d6 10. Nbd2 O-O 11. Nb3 Nd7 12. Be3 Rc8 13. Rc1 h6 14. Nfd2 f5 15. f4 Kh7 16. Qe2 cxb4 17. axb4 exf4 18. Bxf4 Rxc3 19. Rxc3 Bxc3 20. Bxd6 Qb6+ 21. Bc5 Nxc5 22. bxc5 Qe6 23. d4 Rd8 24. Qd3 Bxd2 25. Nxd2 fxe4 26. Nxe4 Nf5 27. d5 Qe5 28. g4 Ne7 29. Rf7+ Kg8 30. Qf1 Nxd5 31. Rxb7 Qd4+ 32. Kh1 Rf8 33. Qg1 Ne3 34. Re7 a5 35. c6 a4 36. Qxe3 Qxe3 37. Nf6+ Rxf6 38. Rxe3 Rd6 39. h4 Rd1+ 40. Kh2 b4 41. c7 
    """
    
    analyzer = ChessAnalyzer()
    try:
        analysis = analyzer.analyzeGame(pgnString)
        analyzer.displayAnalysis(analysis)
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()