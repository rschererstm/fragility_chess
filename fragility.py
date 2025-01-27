import chess
import chess.pgn
import networkx as nx
import re
import argparse

parser = argparse.ArgumentParser(description='Calculate fragility and evaluation scores from a PGN file.')
parser.add_argument('filepath', type=str, help='Path to the PGN file')
args = parser.parse_args()
file_path = args.filepath


def build_interaction_graph(board):
    """
    Build the directed interaction graph G for the given board position.
    
    - Nodes: one per piece on the board, labeled (square, piece).
    - Directed Edges:
        * Attack: p_i -> p_j if piece at p_i can capture piece at p_j.
        * Defense: p_i -> p_j if p_i and p_j are same color and p_i can move to p_j's square.
    """
    G = nx.DiGraph()
    
    piece_map = board.piece_map()  # dict[square -> Piece]
    for square_i, piece_i in piece_map.items():
        G.add_node((square_i, piece_i))
    
    for square_i, piece_i in piece_map.items():
        attacked_squares = board.attacks(square_i)
        for square_j in attacked_squares:
            if square_j in piece_map:
                piece_j = piece_map[square_j]
                if piece_i.color == piece_j.color:
                    # Defense edge
                    G.add_edge((square_i, piece_i), (square_j, piece_j), interaction="defense")
                else:
                    # Attack edge
                    G.add_edge((square_i, piece_i), (square_j, piece_j), interaction="attack")
    
    return G


def compute_fragility_score(board):
    """
    Given a chess.Board position, build the interaction graph, compute BC, and
    return a tuple:
      (fragility_score, top_piece)
    where:
      - fragility_score = sum of BC of all attacked pieces
      - top_piece = the (square, piece) with the highest BC among attacked pieces 
                    (or None if no attacked piece).
    """
    G = build_interaction_graph(board)
    if len(G) == 0:
        return 0.0, None
    
    bc = nx.betweenness_centrality(G, normalized=False)
    
    attacked_nodes = set()
    for u, v, data in G.edges(data=True):
        if data.get("interaction") == "attack":
            attacked_nodes.add(v)
    
    if not attacked_nodes:
        return 0.0, None  # no piece is under attack => no fragility
    
    # Sum the BC of all attacked nodes => total fragility
    fragility = sum(bc[node] for node in attacked_nodes)
    
    # Find the piece with highest BC among attacked nodes
    top_node = max(attacked_nodes, key=lambda node: bc[node])
    # top_node is (square, piece)
    
    return fragility, top_node


def extract_eval(comment):
    """
    Extracts the [%eval value] from the PGN comment string if it exists.
    Returns None if no evaluation is found.
    """
    match = re.search(r"\[%eval ([+-]?[0-9.]+|#-?\d+)\]", comment)
    if match:
        eval_str = match.group(1)
        # Example match: "0.56", "-1.20", "#3", "#-4", etc.
        if "#" in eval_str:
            return eval_str  # Mate notation like #3 or #-5
        return float(eval_str)  # Centipawn (float)
    return None


def fragility_and_eval_by_ply(pgn_file):
    """
    Given a PGN file, return a list of:
      (ply_number, move_uci, fragility_score, eval_score, top_node)
    """
    # Parse the first game
    game = chess.pgn.read_game(pgn_file)
    if game is None:
        raise ValueError("No valid game found in PGN.")
    
    board = game.board()
    node = game

    results = []
    ply_count = 0
    
    # Initial position
    current_frag, top_piece = compute_fragility_score(board)
    results.append((ply_count, None, current_frag, None, top_piece))
    
    while not node.is_end():
        next_node = node.variation(0)
        move = next_node.move
        
        board.push(move)
        ply_count += 1
        
        current_frag, top_piece = compute_fragility_score(board)
        
        comment = next_node.comment
        eval_score = extract_eval(comment)
        
        # Move in UCI
        move_uci = move.uci()
        
        results.append((ply_count, move_uci, current_frag, eval_score, top_piece))
        
        node = next_node
    
    return results


if __name__ == "__main__":
    with open(file_path, "r") as pgn_file:
        scores = fragility_and_eval_by_ply(pgn_file)
    
    cumulative_eval = 0.0
    
    print("Ply | Move    | Fragility | Eval  | TopAttackedPiece      | CumulativeEval")
    print("--------------------------------------------------------------------------")
    for ply_num, move_uci, frag_score, eval_score, top_node in scores:
        if move_uci is None:
            move_uci = "start-pos"
        # Show eval
        eval_display = f"{eval_score:+.2f}" if isinstance(eval_score, float) else str(eval_score)
        
        # If we have a numeric evaluation, add to cumulative
        if isinstance(eval_score, float):
            cumulative_eval += eval_score
        
        # Convert top_node (square, piece) into a short string
        if top_node is not None:
            sq, pc = top_node
            top_node_str = f"{pc.symbol()}@{chess.square_name(sq)}"
        else:
            top_node_str = "-"
        ply_num = ply_num // 2
        print(f"{ply_num:3d} | {move_uci:8s} | {frag_score:9.3f} | {eval_display:5s} | {top_node_str:20s} | {cumulative_eval:+.2f}")
