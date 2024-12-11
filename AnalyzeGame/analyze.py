import os
import chess
import chess.engine
import chess.pgn
import io
import sys
import json

#FIX ISSUE: IT SHOWS ITSELF AS A FORCING MOVE THAT IT LED TO
#   - because it's not counting correctly, it's one ahead behind (it thinks 15 is 14)

class ChessAnalyzer:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        self.engine = chess.engine.SimpleEngine.popen_uci(config['engine_path'])
        self.critical_moments = []

    def findCriticalMoment(self, analysis, current_index, move, board):
        if current_index < 2:  
            return

        move_number = (current_index // 2) + 1  
        if move is not None:
            print(f"FORCED MOVE: {move_number} {current_index + 1} {board.san(move)}")
        else:
            print(f"FORCED MOVE: {move_number} {current_index + 1} (none)")

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
        

        
    
    def analyzeGame(self, pgn_string, time_per_move=1.0, cache_file='analysis_cache.json'):
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as file:
                    serialized_analysis, self.critical_moments = json.load(file)
                    self.analysis = self.deserialize_analysis(serialized_analysis)
                return self.analysis, self.critical_moments
            except json.JSONDecodeError:
                print(f"Warning: Cache file {cache_file} is corrupted. Recomputing analysis.")
                os.remove(cache_file)
        game = chess.pgn.read_game(io.StringIO(pgn_string))
        analysis = []
        
        board = game.board()
        move_count = 0

        for move in list(game.mainline_moves()) + [None]:
            if move is not None:
                info = self.engine.analyse(board, chess.engine.Limit(time=time_per_move), multipv=5)

                print(board.san(move), move_count)

                # See if this move is forced (50 points better than the next best move)
                forcing_moves = []
                if len(info) > 0:
                    top_sequence = info[0]["pv"]
                    top_score = info[0]["score"].relative.score(mate_score=10000)
                    top_score2nd = info[1]["score"].relative.score(mate_score=10000)

                    if abs(top_score - top_score2nd) > 50:
                        self.findCriticalMoment(analysis, len(analysis) - 1, move, board)
                        forcing_moves.append(top_sequence[0])

                # Add sequences to analysis for gui
                top_sequences = []
                for i in range(min(5, len(info))):
                    sequence = info[i]["pv"]
                    score = info[i]["score"].white().score(mate_score=10000)
                    top_sequences.append((score, sequence))
                print(); print(top_sequences); print()

                # Calculate A-score
                best_score = top_sequences[0][0]
                fifth_score = top_sequences[4][0] if len(top_sequences) >= 5 else best_score
                a_score = abs(best_score - fifth_score) if best_score != 0 else 0

                # Calculate B-score
                b_score = None
                current_index = move_count
                if len(analysis) > 1:  # Need at least 2 moves for comparison
                    if current_index % 2 == 0:  # White's move
                        if current_index >= 2 and 'a_score' in analysis[-2]:
                            prev_a_score = analysis[-2]['a_score']
                            if prev_a_score != 0:
                                b_score = (a_score - prev_a_score) / prev_a_score
                    else:  # Black's move
                        if current_index >= 2 and 'a_score' in analysis[-2]:
                            prev_a_score = analysis[-2]['a_score']
                            if prev_a_score != 0:
                                b_score = (a_score - prev_a_score) / prev_a_score

                # Append the analysis for the current move
                analysis.append({
                    'move': (board.san(move), move_count),
                    'fen': board.fen(),
                    'top_sequences': top_sequences,
                    'forcing_moves': (forcing_moves, move_count),
                    'a_score': a_score,
                    'b_score': b_score
                })

                # Move the board to the next move state
                board.push(move)
            else:
                print("Game over", move_count)
                # Append the analysis for the game over state
                analysis.append({
                    'move': ("Game over", move_count),
                    'fen': board.fen(),
                    'top_sequences': [],
                    'forcing_moves': ([], move_count)
                })
            move_count += 1
        
        with open(cache_file, 'w') as file:
            json.dump((self.serialize_analysis(analysis), self.critical_moments), file)

        return analysis, self.critical_moments
    
    def serialize_analysis(self, analysis):
        serialized = []
        for entry in analysis:
            serialized_entry = entry.copy()
            serialized_entry['top_sequences'] = [
                (score, [move.uci() for move in sequence])
                for score, sequence in entry['top_sequences']
            ]
            serialized_entry['forcing_moves'] = (
                [move.uci() for move in entry['forcing_moves'][0]],
                entry['forcing_moves'][1]
            )
            serialized.append(serialized_entry)
        return serialized

    def deserialize_analysis(self, serialized_analysis):
        analysis = []
        for entry in serialized_analysis:
            deserialized_entry = entry.copy()
            deserialized_entry['top_sequences'] = [
                (score, [chess.Move.from_uci(move) for move in sequence])
                for score, sequence in entry['top_sequences']
            ]
            deserialized_entry['forcing_moves'] = (
                [chess.Move.from_uci(move) for move in entry['forcing_moves'][0]],
                entry['forcing_moves'][1]
            )
            analysis.append(deserialized_entry)
        return analysis
    def close(self):
        self.engine.quit()


def main():
    #pgn_string = "1.e4 c5 2.Nf3 a6 3.d3 g6 4.g3 Bg7 5.Bg2 b5 6.O-O Bb7 7.c3 e5 8.a3 Ne7 9.b4 d6 10.Nbd2 O-O 11.Nb3 Nd7 12.Be3 Rc8 13.Rc1 h6 14.Nfd2 f5 15.f4 Kh7 16.Qe2 cxb4 17.axb4 exf4 18.Bxf4 Rxc3 19.Rxc3 Bxc3 20.Bxd6 Qb6+ 21.Bc5 Nxc5 22.bxc5 Qe6 23.d4 Rd8 24.Qd3 Bxd2 25.Nxd2 fxe4 26.Nxe4 Nf5 27.d5 Qe5 28.g4 Ne7 29.Rf7+ Kg8 30.Qf1 Nxd5 31.Rxb7 Qd4+ 32.Kh1 Rf8 33.Qg1 Ne3 34.Re7 a5 35.c6 a4 36.Qxe3 Qxe3 37.Nf6+ Rxf6 38.Rxe3 Rd6 39.h4 Rd1+ 40.Kh2 b4 41.c7  1-0"
    pgn_string = "1. e4 f6 2. d4 g5 3. Qh5#"
    #pgn_string = "1. d4 d5 2. c4 Nf6 { D06 Queen's Gambit Declined: Marshall Defense } 3. cxd5 Nxd5 4. e4 Nf6 5. Nc3 e6 6. Nf3 Bb4 7. Bd3 Bxc3+ 8. bxc3 O-O 9. O-O b6 10. Bg5 Nbd7 11. e5 h6 12. Bxh6 gxh6 13. exf6 Qxf6 14. Be4 Rb8 15. Qa4 a5 16. Bc6 Rd8 17. Rae1 Nf8 18. Ne5 Bb7 19. Re3 Bxc6 20. Nxc6 Rdc8 21. Nxb8 Rxb8 22. Qb5 Ng6 23. Rf3 Qe7 24. Qc6 Rd8 25. Qe4 Rd5 26. Rg3 Rg5 27. Rxg5 Qxg5 28. Re1 Qd2 29. Qe3 Qxa2 30. Qxh6 Qc2 31. Qe3 a4 32. g3 a3 33. Re2 Qb1+ 34. Re1 Qb3 35. Qc1 a2 36. Kg2 Ne7 37. Re2 Nd5 38. Qa1 Nxc3 39. Re3 Qb1 40. Qxc3 a1=Q { Black wins on time. } 0-1"
    analyzer = ChessAnalyzer()
    analyzer.analyzeGame(pgn_string)
    analyzer.close()


if __name__ == "__main__":
    main()
