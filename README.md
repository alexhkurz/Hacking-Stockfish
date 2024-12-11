# README

Create a file `AnalyzeGame/config.json` containing the path to the Stockfish executable:

```json
{
    "engine_path": "/Users/.../Stockfish/src/stockfish"
}
```

Then run `python analyze.py` in the `AnalyzeGame` directory.

## Features Added to `analyze.py`

- Save the last analysis to `analysis_cache.json`.
- If `analysis_cache.json` exists, load it instead of recreating the analysis.
- A-score
- B-score 

## Features Added to `gui.py`

- Play through the history using right and left arrow keys.
- Jump to the start or end of the game using up and down arrow keys.
- Save and load analysis to a file.
- Display the A-score and B-score for each move.

