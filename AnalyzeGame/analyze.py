import chess
import chess.engine
import chess.pgn
import io
import sys

#FIX ISSUE: IT SHOWS ITSELF AS A FORCING MOVE THAT IT LED TO
#   - because it's not counting correctly, it's one ahead behind (it thinks 15 is 14)


class ChessAnalyzer:
    def __init__(self, engine_path="/Users/kevinhuang/Documents/Projects/Hacking-Stockfish/Stockfish/src/stockfish"):
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.critical_moments = []

    def findCriticalMoment(self, analysis, current_index, move, board):
        if current_index < 2:  
            return

        move_number = (current_index // 2) + 1  
        print(f"FORCED MOVE: {move_number} {current_index + 1} {board.san(move)}")

        current_color = "White" if current_index % 2 == 0 else "Black"
        current_analysis = analysis[current_index]
        current_good_options = sum(1 for score, _ in current_analysis['top_sequences'] if abs(score - current_analysis['top_sequences'][0][0]) <= 100)
        is_forcing_move = len(current_analysis['forcing_moves'][0]) > 0
        
        if is_forcing_move:
            for i in range(current_index - 2, -1, -2):  # Count backwards by 2
                earlier_analysis = analysis[i]
                earlier_good_options = sum(1 for score, _ in earlier_analysis['top_sequences'] if abs(score - earlier_analysis['top_sequences'][0][0]) <= 100)
                earlier_good_move = earlier_analysis['move'][0]
                earlier_move_number = (i // 2) + 1
                print(f"   -ITERATING BACKWARDS TO FIND A CRITICAL MOMENT {earlier_move_number} {i + 1} {earlier_good_move}")
                
                if earlier_good_options > current_good_options:
                    print(f"   -FOUND CRITICAL MOMENT: {earlier_move_number} {i + 1} {earlier_good_move}")
                    self.critical_moments.append({
                        'type': 'critical_move',
                        'move_number': move_number,
                        'color': current_color,
                        'move': current_analysis['move'][0],
                        'description': f"{current_analysis['move'][0]} is a forced move that came from {earlier_good_move} (move {earlier_move_number}), reducing options from {earlier_good_options} to {current_good_options}"
                    })
                    break
        

        
    
    def analyzeGame(self, pgn_string, time_per_move=1.0):
        game = chess.pgn.read_game(io.StringIO(pgn_string))
        analysis = []
        
        board = game.board()
        move_count = 0

        for move in game.mainline_moves():
            info = self.engine.analyse(board, chess.engine.Limit(time=time_per_move), multipv=5)

            print(board.san(move), move_count)

            #See if this move is forced (50 points better than the next best move)
            forcing_moves = []
            if len(info) > 0:
                top_sequence = info[0]["pv"]
                top_score = info[0]["score"].relative.score(mate_score=10000)
                top_score2nd = info[1]["score"].relative.score(mate_score=10000)                

                if abs(top_score - top_score2nd) > 50:
                    self.findCriticalMoment(analysis, len(analysis)-1, move, board)
                    forcing_moves.append(top_sequence[0])

            #Add sequences to analysis for gui
            top_sequences = []
            for i in range(min(5, len(info))):
                sequence = info[i]["pv"]
                score = info[i]["score"].relative.score(mate_score=10000)
                top_sequences.append((score, sequence))

            #Append the analysis for the current move
            analysis.append({
                'move': (board.san(move), move_count),
                'fen': board.fen(),
                'top_sequences': top_sequences,
                'forcing_moves': (forcing_moves, move_count)
            })


            #Move the board to the next move state 
            board.push(move)
            move_count += 1
        
        return analysis, self.critical_moments
    
    def close(self):
        self.engine.quit()


def main():
    pgn_string = "1.e4 c5 2.Nf3 a6 3.d3 g6 4.g3 Bg7 5.Bg2 b5 6.O-O Bb7 7.c3 e5 8.a3 Ne7 9.b4 d6 10.Nbd2 O-O 11.Nb3 Nd7 12.Be3 Rc8 13.Rc1 h6 14.Nfd2 f5 15.f4 Kh7 16.Qe2 cxb4 17.axb4 exf4 18.Bxf4 Rxc3 19.Rxc3 Bxc3 20.Bxd6 Qb6+ 21.Bc5 Nxc5 22.bxc5 Qe6 23.d4 Rd8 24.Qd3 Bxd2 25.Nxd2 fxe4 26.Nxe4 Nf5 27.d5 Qe5 28.g4 Ne7 29.Rf7+ Kg8 30.Qf1 Nxd5 31.Rxb7 Qd4+ 32.Kh1 Rf8 33.Qg1 Ne3 34.Re7 a5 35.c6 a4 36.Qxe3 Qxe3 37.Nf6+ Rxf6 38.Rxe3 Rd6 39.h4 Rd1+ 40.Kh2 b4 41.c7  1-0"
    analyzer = ChessAnalyzer()
    analyzer.analyzeGame(pgn_string)
    analyzer.close()


if __name__ == "__main__":
    main()
