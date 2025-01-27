# Chess Fragility Score in Chess

<div style="display: flex; justify-content: center; align-items: center; gap: 10px;">
  <img src="https://github.com/user-attachments/assets/2c2dcf4b-3e22-41ca-980f-e317e5957dca" alt="Image 1" width="300" height="300">
  <img src="https://github.com/user-attachments/assets/bfbb6630-d76b-453a-a93d-bef78f783395" alt="Image 2" width="300" height="300">
</div>


This repository provides a Python script that reads a single chess game from a PGN file and computes:

1. **Fragility Score** at each half-move (ply), as defined in the paper  
   [*“Fragility of chess positions: Measure, universality, and tipping points”* (Barthelemy, Phys. Rev. E, 2025)](https://journals.aps.org/pre/pdf/10.1103/PhysRevE.111.014314).  
   - The **fragility** of a position is based on constructing a directed *attack/defense* graph of pieces and summing the Betweenness Centrality of any pieces that are under attack.

2. **Highest-Fragility Piece** (the piece under attack with the largest betweenness centrality) at each position—helpful for identifying which single piece is the most “critical.”

3. **Engine Evaluation** scores (`[%eval ...]`) embedded in PGN comments, commonly added by sites like Lichess.

The concept of fragility and tipping points in chess has also been highlighted in a popular-science article on [Ars Technica](https://arstechnica.com/science/2025/01/complexity-physics-finds-crucial-tipping-points-in-chess-games/#:~:text=He%20also%20calculated%20so%2Dcalled,over%20the%20last%20200%20years.).

---

## Table of Contents

1. [Features](#features)  
2. [Installation](#installation)  
3. [Usage](#usage)  
4. [Explanation of Output](#explanation-of-output)  
5. [References](#references)  
6. [License](#license)

---

## Features

- **Fragility Score**: Summation of betweenness centrality of all attacked pieces in a given position.  
- **Highest-Fragility Piece**: Shows which attacked piece has the greatest betweenness centrality.  
- **Evaluation Extraction**: Reads engine evaluations from PGN comments in the form `[ %eval ... ]`.  
- **Cumulative Eval**: Keeps a running total of numeric engine evals as the game progresses.  

---

## Installation

1. **Clone** (or download) this repository:

   ```bash
   git clone https://github.com/yourusername/chess-fragility-eval.git
   cd chess-fragility-eval
   ```

2. **Create a virtual environment** (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install chess networkx
   ```

   If you plan to parse command-line arguments exactly as shown, you’ll also need `argparse` (though it’s usually part of the Python standard library).

---

## Usage

1. **Prepare a PGN file** containing exactly one chess game. (If multiple games are in the same file, the script only processes the first.) [Export your PGN with annotation to get the 'Eval' column]
2. **Run** the script with:

   ```bash
   python fragility.py /path/to/game.pgn
   ```

   - `fragility.py` is the Python file containing the code shown above.  
   - `/path/to/game.pgn` is the PGN file you want to analyze.

The script will read the game, compute fragility scores and engine evaluations for each ply, and print the results to standard output.

---

## Explanation of Output

The program prints a table with columns:

```
Ply | Move    | Fragility | Eval  | TopAttackedPiece      | CumulativeEval
--------------------------------------------------------------------------
  0 | start-pos |     0.000 | None  | -                    |  +0.00
  0 | e2e4     |     4.571 | +0.50 | Q@d1                 |  +0.50
  1 | d7d5     |     3.225 | +0.60 | n@f6                 |  +1.10
  ...
```

Here’s what each column represents:

1. **Ply** – The half-move index, integer-divided by 2 to display full-move count if you prefer (e.g., ply=0 means before any move; ply=1 means after White’s 1st move).  
2. **Move** – The move in UCI notation (e.g., `e2e4`). “start-pos” indicates the initial position before any move is played.  
3. **Fragility** – The total *fragility score* of the position. Higher means more crucial pieces (with high betweenness centrality) are under attack.  
4. **Eval** – The engine evaluation from PGN comments, if any. Can be a float (e.g., `+0.50`) or a mate notation (e.g., `#3`). If not found, it shows `None`.  
5. **TopAttackedPiece** – The single attacked piece with the highest betweenness centrality, displayed as `X@sq`, where `X` is the piece symbol, and `sq` is the board square. `-` if no piece is attacked.  
6. **CumulativeEval** – A running sum of the numeric evals (ignoring mate notation). For instance, if the engine eval was +0.50 and then +0.60, the cumulative is +1.10.  

---

## References

1. **Original Paper**  
   *Marc Barthelemy*, “Fragility of chess positions: Measure, universality, and tipping points,”  
   [*Phys. Rev. E **111**, 014314 (2025)*](https://journals.aps.org/pre/pdf/10.1103/PhysRevE.111.014314).

2. **Popular-Science Article**  
   [Python code for computing the fragility score during a chess game (Phys. Rev. E 111, 014314)](https://arstechnica.com/science/2025/01/complexity-physics-finds-crucial-tipping-points-in-chess-games/#:~:text=He%20also%20calculated%20so%2Dcalled,over%20the%20last%20200%20years.)

3. **Original Jupyter [shared now]**  
   [Ars Technica: Complexity physics finds crucial tipping points in chess games](https://zenodo.org/records/14742727)


---

## License

This code is made available under the terms of the MIT License. You are free to use, modify, and distribute it as you wish. If you use it in academic research or software, please consider referencing the original paper above. Enjoy analyzing the **fragility** of chess!
