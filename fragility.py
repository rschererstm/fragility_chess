import chess
import chess.pgn
import networkx as nx
import re
import argparse

parser = argparse.ArgumentParser(description='Calculate fragility and evaluation scores from a PGN file.')
parser.add_argument('filepath', type=str, help='Path to the PGN file')
args = parser.parse_args()
file_path = args.filepath

def compute_interactions_for_color(board, color_turn):
    """
    Builds a subgraph of interactions (attack/defense) **only** for the color 'color_turn'.
    Returns a networkx DiGraph with colored edges:
      - 'red' for attack,
      - 'blue' (if color_turn is WHITE) or 'green' (if color_turn is BLACK) for defense.
    The nodes are (square, piece).
    """
    G = nx.DiGraph()
    
    # List of all pieces on the board
    piece_positions = {sq: board.piece_at(sq) for sq in chess.SQUARES if board.piece_at(sq)}
    
    # To ensure the current turn is 'color_turn'
    board_copy = board.copy()
    board_copy.turn = color_turn

    # Add all nodes (regardless of color) so they can appear as edge targets
    for sq, pc in piece_positions.items():
        G.add_node((sq, pc))
    
    # For each piece of the color 'color_turn', check possible attacks/defenses
    for square_a, piece_a in piece_positions.items():
        if piece_a.color == color_turn:
            # Iterate over all other squares
            for square_b, piece_b in piece_positions.items():
                if square_b == square_a:
                    continue

                # Define nodes as (sq, piece)
                node_a = (square_a, piece_a)
                node_b = (square_b, piece_b)

                # Defense (same color)
                if piece_b.color == piece_a.color:
                    # To check if it is really possible to "defend" that piece
                    # (i.e., if it would move to that square in a legal move)
                    backup_piece = board_copy.remove_piece_at(square_b)
                    move = chess.Move(from_square=square_a, to_square=square_b)
                    if move in board_copy.legal_moves:
                        # The edge color follows the convention of code 1:
                        # - 'blue' if it is White,
                        # - 'green' if it is Black.
                        edge_color = 'blue' if color_turn == chess.WHITE else 'green'
                        G.add_edge(node_a, node_b, color=edge_color, interaction='defense')
                    # Put the piece back on square_b
                    if backup_piece is not None:
                        board_copy.set_piece_at(square_b, backup_piece)

                # Attack (different colors)
                else:
                    # Special treatment for pawns: they only capture diagonally if there is an enemy piece on that diagonal
                    if piece_a.piece_type == chess.PAWN:
                        if piece_b is not None:  # there is an opposite color piece
                            move = chess.Move(from_square=square_a, to_square=square_b)
                            if move in board_copy.legal_moves:
                                G.add_edge(node_a, node_b, color='red', interaction='attack')
                    else:
                        # For non-pawn pieces, we directly check if the move is legal
                        move = chess.Move(from_square=square_a, to_square=square_b)
                        if move in board_copy.legal_moves:
                            G.add_edge(node_a, node_b, color='red', interaction='attack')
    
    return G


def build_interaction_graph(board):
    """
    Builds the complete interaction graph by combining (via nx.compose) the graph of
    white pieces and the graph of black pieces, following the logic of the first code.
    """
    G_white = compute_interactions_for_color(board, chess.WHITE)
    G_black = compute_interactions_for_color(board, chess.BLACK)
    G_full = nx.compose(G_white, G_black)
    return G_full


def compute_fragility_score(board):
    """
    Calculates the fragility score using the same logic as the first code:
      - Builds the interaction graph (attack/defense);
      - Calculates Betweenness Centrality (normalized);
      - Identifies nodes that are under attack (receive 'red' edge);
      - Sum of the BCs of these nodes => fragility score;
      - top_piece => node (square, piece) with the highest BC among those attacked.
    """
    G = build_interaction_graph(board)

    # If there are no nodes in the graph, fragility is 0
    if len(G) == 0:
        return 0.0, None
    
    # Normalized betweenness centrality
    bc = nx.betweenness_centrality(G, normalized=True)
    
    # Identify pieces under attack (nodes that receive 'red' edge)
    attacked_nodes = set()
    for u, v, data in G.edges(data=True):
        if data.get("color") == "red":
            attacked_nodes.add(v)
    
    if not attacked_nodes:
        return 0.0, None
    
    # Fragility score: sum of the BC of the attacked pieces
    fragility = sum(bc[node] for node in attacked_nodes)
    
    # top_piece: the attacked piece with the highest BC
    top_node = max(attacked_nodes, key=lambda node: bc[node])
    
    return fragility, top_node


def extract_eval(comment):
    """
    Extracts the evaluation value (in the format [%eval ...]) from the comment, if it exists.
    Returns None if not found.
    Possible matches examples: 
      0.56, -1.20, #3 (mate in 3), #-4 (mate for the opposite side) etc.
    """
    match = re.search(r"\[%eval ([+-]?[0-9.]+|#-?\d+)\]", comment)
    if match:
        eval_str = match.group(1)
        if "#" in eval_str:
            return eval_str  # mate notation (#3, #-5, etc.)
        return float(eval_str)  # numeric evaluation (float)
    return None


def fragility_and_eval_by_ply(pgn_file):
    """
    Reads the first game from the PGN file and returns a list of tuples:
      (ply_number, move_uci, fragility_score, eval_score, top_node)
    where:
      - ply_number is the move number (starting at 0 before any move)
      - move_uci is the move in UCI or 'start-pos' if it is the initial position
      - fragility_score is the value calculated by the sum of the BCs of the pieces under attack
      - eval_score is the evaluation value extracted from the comment (None if not found)
      - top_node is the piece (square, piece) with the highest BC among those under attack
    """
    game = chess.pgn.read_game(pgn_file)
    if game is None:
        raise ValueError("No valid game was found in the PGN.")
    
    board = game.board()
    node = game

    results = []
    ply_count = 0
    
    # Initial position (before any move)
    current_frag, top_piece = compute_fragility_score(board)
    results.append((ply_count, "start-pos", current_frag, None, top_piece))
    
    # Iterate over the main line of moves
    while not node.is_end():
        next_node = node.variation(0)
        move = next_node.move
        
        board.push(move)
        ply_count += 1
        
        current_frag, top_piece = compute_fragility_score(board)
        
        comment = next_node.comment
        eval_score = extract_eval(comment)
        
        move_uci = move.uci()
        
        results.append((ply_count, move_uci, current_frag, eval_score, top_piece))
        
        node = next_node
    
    return results


if __name__ == "__main__":    
    with open(file_path, "r") as pgn_file:
        scores = fragility_and_eval_by_ply(pgn_file)
    
    cumulative_eval = 0.0
    
    print("Ply | Move      | Fragility  | Eval   | TopAttackedPiece     | CumulativeEval")
    print("----------------------------------------------------------------------------")
    for ply_num, move_uci, frag_score, eval_score, top_node in scores:
        # Display the move
        if move_uci is None:
            move_uci = "start-pos"
        
        # Format the evaluation
        eval_display = f"{eval_score:+.2f}" if isinstance(eval_score, float) else str(eval_score)
        
        # Cumulative sum if numeric
        if isinstance(eval_score, float):
            cumulative_eval += eval_score
        
        # If there is a top_node, format something like "P@e4"
        if top_node is not None:
            sq, pc = top_node
            top_node_str = f"{pc.symbol()}@{chess.square_name(sq)}"
        else:
            top_node_str = "-"
        
        # Note that we are printing the actual ply (ply_num),
        # but you can divide by 2 if you want the "chess move number".
        print(f"{ply_num:3d} | {move_uci:9s} | {frag_score:10.3f} | {eval_display:6s} | {top_node_str:20s} | {cumulative_eval:+.2f}")
