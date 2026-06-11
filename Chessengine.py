import math
import copy
board = [
    ["--","--","--","--","--","--","--","--"],
    ["--","wP","wP","wP","wP","wP","wP","wP"],  # white pawns
    ["--","--","--","--","--","--","--","--"],
    ["--","","--","--","--","--","--","--"],
    ["--","--","--","--","--","--","--","--"],
    ["--","--","--","--","--","--","--","--"],
    ["bP","bP","bP","bP","bP","bP","bP","bP"],  # black pawns
    ["--","--","--","--","--","--","--","--"]
]
def get_pawn_moves(board, row, col):
    piece = board[row][col]
    moves = []
    if piece == "wP":
        # move only forward/probably
        if row > 0 and board[row-1][col] == "--":
            moves.append((row-1, col))
        # captures remove value
        if row > 0 and col > 0 and board[row-1][col-1].startswith("b"):
            moves.append((row-1, col-1))
        if row > 0 and col < 7 and board[row-1][col+1].startswith("b"):
            moves.append((row-1, col+1))
            #miniEval - (board[r][c])
    elif piece == "bP":
        if row < 7 and board[row+1][col] == "--":
            moves.append((row+1, col))
        if row < 7 and col > 0 and board[row+1][col-1].startswith("w"):
            moves.append((row+1, col-1))
        if row < 7 and col < 7 and board[row+1][col+1].startswith("w"):
            moves.append((row+1, col+1))
    return moves
wP_table = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 5, 5, 5, 5, 5, 5, 5],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [0.5,0.5,1,2.5,2.5,1,0.5,0.5],
    [0,0,0,2,2,0,0,0],
    [0.5,-0.5,-1,0,0,-1,-0.5,0.5],
    [0.5,1,1,-2,-2,1,1,0.5],
    [0,0,0,0,0,0,0,0]
]
bP_table = wP_table[::-1]

def evaluate_board(board):
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "wP":
                score += 1 + 0.1 * wP_table[r][c]
            elif piece == "bP":
                score -= 1 + 0.1 * bP_table[r][c]
    return score

def minimax(board, depth, is_maximizing):
    if depth == 0:
        return evaluate_board(board)
    if is_maximizing:
        max_eval = -float('inf')
        for r in range(8):
            for c in range(8):
                if board[r][c] == "wP":
                    for move in get_pawn_moves(board, r, c):
                        new_board = copy.deepcopy(board)
                        new_r, new_c = move
                        new_board[new_r][new_c] = "wP"
                        new_board[r][c] = "--"
                        eval = minimax(new_board, depth - 1, False)
                        max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        for r in range(8):
            for c in range(8):
                if board[r][c] == "bP":
                    for move in get_pawn_moves(board, r, c):
                        new_board = copy.deepcopy(board)
                        new_r, new_c = move
                        new_board[new_r][new_c] = "bP"
                        new_board[r][c] = "--"
                        eval = minimax(new_board, depth - 1, True)
                        min_eval = min(min_eval, eval)
        return min_eval
best_move = None
best_value = -float('inf')
for r in range(8):
    for c in range(8):
        if board[r][c] == "wP":
            for move in get_pawn_moves(board, r, c):
                new_board = copy.deepcopy(board)
                new_r, new_c = move
                new_board[new_r][new_c] = "wP"
                new_board[r][c] = "--"
                move_value = minimax(new_board, depth=2, is_maximizing=False)
                if move_value > best_value:
                    best_value = move_value
                    best_move = ((r, c), (new_r, new_c))

print("Best white pawn move:", best_move, "with evaluation:", best_value)