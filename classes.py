import pygame as pg
import os

_display_available = os.environ.get("SDL_VIDEODRIVER") != "works"

# No update for server
def _load_image(path):
    try:
        return pg.image.load(path)
    except:
        surf = pg.Surface((64, 64))
        surf.fill((128, 128, 128))
        return surf

class Move:
    def __init__(self, start, end):
        self.start = start
        self.end = end # parse to json

    def to_dict(self):
        return {"start": list(self.start), "end": list(self.end)}
        #self.start : self.end
    @classmethod
    def from_dict(cls, d):  #classmethod
        return cls(tuple(d["start"]), tuple(d["end"]))
class Game_State:
    def __init__(self):
        self.board = [
            [
                Castle("assets/images/bR.png", "black"),
                Knight("assets/images/bN.png", "black"),
                Bishop("assets/images/bB.png", "black"),
                Queen("assets/images/bQ.png", "black"),
                King("assets/images/bK.png", "black"),
                Bishop("assets/images/bB.png", "black"),
                Knight("assets/images/bN.png", "black"),
                Castle("assets/images/bR.png", "black"),
            ],
            [Pawn("assets/images/bp.png", "black") for _ in range(8)],
            ["--" for _ in range(8)],
            ["--" for _ in range(8)],
            ["--" for _ in range(8)],
            ["--" for _ in range(8)],
            [Pawn("assets/images/wp.png", "white") for _ in range(8)],
            [
                Castle("assets/images/wR.png", "white"),
                Knight("assets/images/wN.png", "white"),
                Bishop("assets/images/wB.png", "white"),
                Queen("assets/images/wQ.png", "white"),
                King("assets/images/wK.png", "white"),
                Bishop("assets/images/wB.png", "white"),
                Knight("assets/images/wN.png", "white"),
                Castle("assets/images/wR.png", "white"),
            ],
        ]

        self.white_pieces = []
        self.black_pieces = []
        self.whiteKing = None
        self.blackKing = None
        self.board_state = None
        self.captured_by_black = []
        self.captured_by_white = []

        for i, row in enumerate(self.board):
            for j, piece in enumerate(row):
                if isinstance(piece, Castle):
                    piece.start_pos = (i, j)

# Serialized
    def to_dict(self):
        board_data = []
        for row in self.board:
            row_data = []
            for piece in row:
                if piece == "--":
                    row_data.append("--")
                else:
                    entry = {
                        "type": piece.__class__.__name__,
                        "color": piece.color,
                    }
                    # Castling flagging
                    if isinstance(piece, (Castle, King)):
                        entry["castling"] = piece.castling
                    if isinstance(piece, Pawn):
                        #Janky Jank
                        entry["en_passant"] = piece.en_passant
                        entry["move_count"] = piece.move_count
                    row_data.append(entry)
            board_data.append(row_data)
        return {"board": board_data}

    def from_dict(self, state):
        # Image paths by type+color
        images = {
            ("Pawn",   "white"): "assets/images/wp.png",
            ("Pawn",   "black"): "assets/images/bp.png",
            ("Castle", "white"): "assets/images/wR.png",
            ("Castle", "black"): "assets/images/bR.png",
            ("Knight", "white"): "assets/images/wN.png",
            ("Knight", "black"): "assets/images/bN.png",
            ("Bishop", "white"): "assets/images/wB.png",
            ("Bishop", "black"): "assets/images/bB.png",
            ("Queen",  "white"): "assets/images/wQ.png",
            ("Queen",  "black"): "assets/images/bQ.png",
            ("King",   "white"): "assets/images/wK.png",
            ("King",   "black"): "assets/images/bK.png",
        }
        type_map = {
            "Pawn": Pawn, "Castle": Castle, "Knight": Knight,
            "Bishop": Bishop, "Queen": Queen, "King": King,
        }

        new_board = []
        for i, row in enumerate(state["board"]):
            board_row = []
            for j, piece_data in enumerate(row):
                if piece_data == "--":
                    board_row.append("--")
                else:
                    t = piece_data["type"]
                    color = piece_data["color"]
                    img = images[(t, color)]
                    piece = type_map[t](img, color)

                    if isinstance(piece, (Castle, King)):
                        piece.castling = piece_data.get("castling", True)
                    if isinstance(piece, Castle):
                        piece.start_pos = (i, j)
                    if isinstance(piece, Pawn):
                        piece.en_passant = piece_data.get("en_passant", False)
                        piece.move_count = piece_data.get("move_count", 0)

                    board_row.append(piece)
            new_board.append(board_row)

        self.board = new_board

        # Rebuild piece lists and king positions
        self.white_pieces.clear()
        self.black_pieces.clear()
        for r, row in enumerate(self.board):
            for c, piece in enumerate(row):
                if piece != "--":
                    if piece.color == "black":
                        if isinstance(piece, King):
                            self.blackKing = (r, c)
                        self.black_pieces.append(piece)
                    else:
                        if isinstance(piece, King):
                            self.whiteKing = (r, c)
                        self.white_pieces.append(piece)


    def get_pos(self, chesspiece):
        for i, row in enumerate(self.board):
            for j, piece in enumerate(row):
                if piece == chesspiece:
                    return (i, j)

    def if_Check(self, turn):
        if turn == "white":
            for piece in self.black_pieces:
                if self.whiteKing in piece.get_moves(self.get_pos(piece), self.board):
                    return True
        elif turn == "black":
            for piece in self.white_pieces:
                if self.blackKing in piece.get_moves(self.get_pos(piece), self.board):
                    return True
        return False

    def squareUnderAttack(self, start, turn):
        valid_moves = []
        piece = self.board[start[0]][start[1]]

        if turn == "white" and piece in self.white_pieces:
            for move in piece.get_moves(start, self.board):
                captured = self.pseudo_move([start, move])
                is_valid = not any(
                    self.whiteKing in p.get_moves(self.get_pos(p), self.board)
                    for p in self.black_pieces
                )
                self.undo_move([start, move], captured)
                if is_valid:
                    valid_moves.append(move)

        elif turn == "black" and piece in self.black_pieces:
            for move in piece.get_moves(start, self.board):
                captured = self.pseudo_move([start, move])
                is_valid = not any(
                    self.blackKing in p.get_moves(self.get_pos(p), self.board)
                    for p in self.white_pieces
                )
                self.undo_move([start, move], captured)
                if is_valid:
                    valid_moves.append(move)

        return valid_moves

    def pseudo_move(self, coords):
        start, end = coords
        piece = self.board[start[0]][start[1]]
        self.board[start[0]][start[1]] = "--"
        captured = self.board[end[0]][end[1]]
        self.board[end[0]][end[1]] = piece

        if isinstance(piece, King):
            if piece.color == "white":
                self.whiteKing = end
            else:
                self.blackKing = end

        if captured in self.white_pieces:
            self.white_pieces.remove(captured)
        elif captured in self.black_pieces:
            self.black_pieces.remove(captured)

        return captured

    def undo_move(self, coords, captured_piece):
        start, end = coords
        piece = self.board[end[0]][end[1]]
        self.board[start[0]][start[1]] = piece
        self.board[end[0]][end[1]] = captured_piece

        if isinstance(piece, King):
            if piece.color == "white":
                self.whiteKing = start
            else:
                self.blackKing = start

        if captured_piece != "--":
            if captured_piece.color == "white":
                self.white_pieces.append(captured_piece)
            else:
                self.black_pieces.append(captured_piece)


# ------------------------------------------------------------------ #
#  Pieces                                                              #
# ------------------------------------------------------------------ #
class Piece:
    def __init__(self, image: str, color: str):
        self.image = _load_image(image)
        self.color = color

    def get_moves(self, pos: tuple, board):
        return []

    def get_valid_moves(self, pos, gs, turn):
        return gs.squareUnderAttack(pos, turn)


class King(Piece):
    def __init__(self, image, color):
        super().__init__(image, color)
        self.start_pos = (7, 4) if color == "white" else (0, 4)
        self.castling = True
        self.check = False

    def get_moves(self, pos, board):
        x, y = pos
        directions = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]
        moves = []
        for dx, dy in directions:
            nx, ny = x+dx, y+dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx][ny] == "--" or board[nx][ny].color != self.color:
                    moves.append((nx, ny))

        if not self.check and pos == self.start_pos and self.castling:
            # Kingside
            if isinstance(board[x][y+3], Castle) and board[x][y+3].castling:
                if board[x][y+1] == "--" and board[x][y+2] == "--":
                    moves.append((x, y+2))
            # Queenside
            if isinstance(board[x][y-4], Castle) and board[x][y-4].castling:
                if board[x][y-1] == "--" and board[x][y-2] == "--" and board[x][y-3] == "--":
                    moves.append((x, y-2))
        return moves

    def get_valid_moves(self, pos, gs, turn):
        valid_moves = sorted(gs.squareUnderAttack(pos, turn))
        l, r = 0, len(valid_moves)
        while l < r:
            col_diff = valid_moves[l][1] - self.start_pos[1]
            if col_diff == 2 and self.castling:
                if (valid_moves[l][0], valid_moves[l][1]-1) not in valid_moves:
                    valid_moves.pop(l); r -= 1; continue
            elif col_diff == -2 and self.castling:
                if (valid_moves[l][0], valid_moves[l][1]+1) not in valid_moves:
                    valid_moves.pop(l); r -= 1; continue
            l += 1
        return valid_moves


class Queen(Piece):
    def __init__(self, image, color):
        super().__init__(image, color)

    def get_moves(self, pos, board):
        x, y = pos
        directions = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]
        moves = []
        for dx, dy in directions:
            nx, ny = x+dx, y+dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx][ny] != "--":
                    if board[nx][ny].color != self.color:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
                nx += dx; ny += dy
        return moves


class Castle(Piece):
    def __init__(self, image, color):
        super().__init__(image, color)
        self.start_pos = None
        self.castling = True

    def get_moves(self, pos, board):
        x, y = pos
        directions = [(1,0),(-1,0),(0,1),(0,-1)]
        moves = []
        for dx, dy in directions:
            nx, ny = x+dx, y+dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx][ny] != "--":
                    if board[nx][ny].color != self.color:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
                nx += dx; ny += dy
        return moves


class Bishop(Piece):
    def __init__(self, image, color):
        super().__init__(image, color)

    def get_moves(self, pos, board):
        x, y = pos
        directions = [(1,1),(-1,1),(1,-1),(-1,-1)]
        moves = []
        for dx, dy in directions:
            nx, ny = x+dx, y+dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx][ny] != "--":
                    if board[nx][ny].color != self.color:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
                nx += dx; ny += dy
        return moves


class Knight(Piece):
    def __init__(self, image, color):
        super().__init__(image, color)

    def get_moves(self, pos, board):
        x, y = pos
        d = 1 if self.color == "white" else -1
        candidates = [
            (x+2*d, y+1),(x+2*d, y-1),(x+1*d, y+2),(x+1*d, y-2),
            (x-1*d, y+2),(x-1*d, y-2),(x-2*d, y+1),(x-2*d, y-1),
        ]
        return [
            m for m in candidates
            if 0 <= m[0] <= 7 and 0 <= m[1] <= 7
            and (board[m[0]][m[1]] == "--" or board[m[0]][m[1]].color != self.color)
        ]


class Pawn(Piece):
    def __init__(self, image, color):
        super().__init__(image, color)
        self.direction = -1 if color == "white" else 1
        self.start_row = 6 if color == "white" else 1
        self.move_count = 0
        self.en_passant = False

    def get_moves(self, pos, board):
        moves = []
        x, y = pos

        # Forward
        if 0 <= x+self.direction <= 7 and board[x+self.direction][y] == "--":
            moves.append((x+self.direction, y))
            if x == self.start_row and board[x+2*self.direction][y] == "--":
                moves.append((x+2*self.direction, y))

        # Captures
        if 0 <= x+self.direction <= 7:
            for dy in [-1, 1]:
                ny = y+dy
                if 0 <= ny <= 7 and board[x+self.direction][ny] != "--":
                    if board[x+self.direction][ny].color != self.color:
                        moves.append((x+self.direction, ny))

        # En passant
        for dy in [-1, 1]:
            ny = y+dy
            if 0 <= ny <= 7 and isinstance(board[x][ny], Pawn):
                if board[x][ny].en_passant:
                    moves.append((x+self.direction, ny))

        return moves


class Squares(pg.sprite.Sprite):
    def __init__(self, x, y, fill):
        super().__init__()
        self.image = pg.Surface((64, 64))
        self.image.fill(fill)
        self.rect = self.image.get_rect()
        self.rect.topleft = [x, y]
        self.original = fill


class Rectangle(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 64
        self.height = 256
        self.x = x
        self.y = y
        self.rect = pg.Rect(
            x*64, 0 if y == 0 else 512-(4*64), self.width, self.height
        )
        color = "white" if y == 0 else "black"
        prefix = "w" if color == "white" else "b"
        self.promotion_pieces = {
            "Queen":  Queen( f"assets/images/{prefix}Q.png", color),
            "Knight": Knight(f"assets/images/{prefix}N.png", color),
            "Rook":   Castle(f"assets/images/{prefix}R.png", color),
            "Bishop": Bishop(f"assets/images/{prefix}B.png", color),
        }

    def display_images(self, screen):
        for i, (_, piece) in enumerate(self.promotion_pieces.items()):
            img_rect = piece.image.get_rect()
            if self.y == 0:
                img_rect.center = (self.x*64+32, i*64+32)
            else:
                img_rect.center = (self.x*64+32, 512-(i*64+32))
            screen.blit(piece.image, img_rect)

    def assign_piece(self, former_piece):
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                x_pos, y_pos = pg.mouse.get_pos()
                click = (x_pos//64, y_pos//64 if self.y == 0 else (512-y_pos)//64)
                if click[0] == self.x:
                    former_piece = self.promotion_pieces[
                        list(self.promotion_pieces.keys())[click[1]]
                    ]
        return former_piece