import pygame as pg
from classes import *
from pygame._sdl2 import Window
import os
import socket
import json
import threading

# --- GUI constants ---
WIDTH = HEIGHT = 700
SQUARE_SIZE = 64
DIMENSION = 8
Y_OFFSET = 128
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
BG_COLOR = (200, 180, 150)
BUTTON_COLOR = (50, 50, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

PIECE_POINTS = {"pawn":1, "knight":3, "bishop":3, "rook":5, "queen":9, "king":0}

os.environ['SDL_VIDEO_CENTERED'] = '1'
pg.init()
screen = pg.display.set_mode((0,0), pg.RESIZABLE)
Window.from_display_module().maximize()
pg.display.set_caption("Over-engineered Chessboard")
clock = pg.time.Clock()
WIN_W, WIN_H = screen.get_size()
BOARD_W = DIMENSION * SQUARE_SIZE
BOARD_H = DIMENSION * SQUARE_SIZE
BOARD_X = (WIN_W - BOARD_W) // 2
BOARD_Y = (WIN_H - BOARD_H) // 2
font = pg.font.SysFont('arial', 32)
small_font = pg.font.SysFont('arial', 24)
turn_font = pg.font.SysFont('Arial', 30)
background_img = pg.image.load("main_screen.jpg")
background_img = pg.transform.scale(background_img, (WIN_W, WIN_H))


def pre_game_screen():
    input_box = pg.Rect((WIN_W//2)-100, WIN_H//2-10, 200, 40)
    color_inactive = GRAY
    color_active = BUTTON_COLOR
    color = LIGHT_BROWN
    active = False
    player_name = ''
    start_game = False
    start_button = pg.Rect(WIN_W//2-60-10, WIN_H//2+50, 60, 40)
    stop_button  = pg.Rect(WIN_W//2+10,    WIN_H//2+50, 60, 40)
    play_button  = pg.Rect(WIN_W//2-30,    WIN_H//2+100, 60, 40)

    while not start_game:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit(); return None, None
            if event.type == pg.MOUSEBUTTONDOWN:
                active = input_box.collidepoint(event.pos)
                color = color_active if active else color_inactive
                if start_button.collidepoint(event.pos) and player_name.strip():
                    return {"name": player_name, "color": "white"}, {"name": "CPU", "color": "black"}
                elif stop_button.collidepoint(event.pos):
                    pg.quit(); return None, None
            if event.type == pg.KEYDOWN and active:
                if event.key == pg.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    player_name += event.unicode

        screen.blit(background_img, (0,0))
        pg.draw.rect(screen, color, input_box, 2)
        screen.blit(font.render(player_name, True, BG_COLOR), (input_box.x+5, input_box.y+5))
        pg.draw.rect(screen, BUTTON_COLOR, start_button)
        pg.draw.rect(screen, BUTTON_COLOR, stop_button)
        pg.draw.rect(screen, BUTTON_COLOR, play_button)
        screen.blit(small_font.render("Start", True, WHITE), (start_button.x+5, start_button.y+5))
        screen.blit(small_font.render("Stop",  True, WHITE), (stop_button.x+5,  stop_button.y+5))
        screen.blit(small_font.render("Play",  True, WHITE), (play_button.x+5,  play_button.y+5))
        pg.display.flip()
        clock.tick(30)


def draw_board(screen):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = LIGHT_BROWN if (row+col) % 2 == 0 else DARK_BROWN
            pg.draw.rect(screen, color,
                         pg.Rect(BOARD_X+col*SQUARE_SIZE, BOARD_Y+row*SQUARE_SIZE,
                                 SQUARE_SIZE, SQUARE_SIZE))


def draw_pieces(screen, gs):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = gs.board[row][col]
            if piece != "--":
                screen.blit(piece.image,
                            (BOARD_X+col*SQUARE_SIZE, BOARD_Y+row*SQUARE_SIZE))


def draw_undo_button(screen):
    rect = pg.Rect(BOARD_X+BOARD_W+20, BOARD_Y+64, 150, 60)
    pg.draw.rect(screen, BLACK, rect)
    screen.blit(turn_font.render("Undo", True, WHITE), (rect.x+20, rect.y+10))
    return rect


def display_turn_and_names(screen, turn, player, cpu,
                           player_points=0, cpu_points=0, in_check=False):
    rect = pg.Rect(BOARD_X+BOARD_W+20, BOARD_Y, 180, 60)
    pg.draw.rect(screen, BLACK, rect)

    # Flash red if the current player is in check
    label = f"Turn: {turn}"
    color = (255, 60, 60) if in_check else WHITE
    screen.blit(turn_font.render(label, True, color), (rect.x+10, rect.y+10))

    text_black = turn_font.render(f"{player['name']} (Black)", True, BLACK)
    text_white = turn_font.render(f"{cpu['name']} (White)", True, WHITE)
    screen.blit(text_black, (BOARD_X, BOARD_Y-50))
    screen.blit(text_white, (BOARD_X+BOARD_W-text_white.get_width(), BOARD_Y-50))
    screen.blit(turn_font.render(f"Points: {player_points}", True, BLACK),
                (rect.x, rect.y+120))
    screen.blit(turn_font.render(f"Points: {cpu_points}", True, WHITE),
                (rect.x, rect.y+160))


def draw_game_over_overlay(screen, message):
    overlay = pg.Surface((BOARD_W, 140), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (BOARD_X, BOARD_Y + BOARD_H//2 - 70))
    msg_surf = font.render(message, True, (255, 215, 0))
    screen.blit(msg_surf, (
        BOARD_X + (BOARD_W - msg_surf.get_width()) // 2,
        BOARD_Y + BOARD_H//2 - 70 + 15
    ))
    sub = small_font.render("Game Over!", True, WHITE)
    screen.blit(sub, (
        BOARD_X + (BOARD_W - sub.get_width()) // 2,
        BOARD_Y + BOARD_H//2 - 70 + 80
    ))


def update_attrs(gs):
    gs.white_pieces.clear()
    gs.black_pieces.clear()
    for r, row in enumerate(gs.board):
        for c, piece in enumerate(row):
            if piece != "--":
                if piece.color == "black":
                    if isinstance(piece, King): gs.blackKing = (r, c)
                    gs.black_pieces.append(piece)
                else:
                    if isinstance(piece, King): gs.whiteKing = (r, c)
                    gs.white_pieces.append(piece)


def run_gui(server_ip="127.0.0.1", server_port=5050):
    global player_points, cpu_points
    player_points = 0
    cpu_points = 0

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client.connect((server_ip, server_port))

    gs = Game_State()
    update_attrs(gs)

    selected_square = None
    turn = "white"
    in_check = False
    running = True
    game_over = False
    game_over_message = None
    state_lock = threading.Lock()

    def listen_server():
        nonlocal turn, game_over, game_over_message, in_check
        buffer = ""
        while True:
            try:
                data = client.recv(4096)
                if not data:
                    break
                buffer += data.decode()
                # Handle multiple jSon messages arriving in one recv
                while buffer:
                    try:
                        state, idx = json.JSONDecoder().raw_decode(buffer)
                        buffer = buffer[idx:].lstrip()
                    except json.JSONDecodeError:
                        break

                    with state_lock:
                        if state.get("game_over"):
                            game_over = True
                            winner = state.get("winner")
                            reason = state.get("reason")
                            if reason == "stalemate":
                                game_over_message = "Stalemate! It's a draw!"
                            else:
                                game_over_message = f"Checkmate! {winner.capitalize()} wins!"
                        else:
                            gs.from_dict(state)
                            if "turn" in state:
                                turn = state["turn"]
                            # Check if the side to move is currently in check
                            in_check = state.get("in_check", False)
            except:
                break

    threading.Thread(target=listen_server, daemon=True).start()

    player, cpu = pre_game_screen()
    if player is None or cpu is None:
        pg.quit()
        return

    while running:
        clock.tick(60)
        screen.fill(BG_COLOR)
        draw_undo_button(screen)

        with state_lock:
            current_turn = turn
            current_check = in_check
            current_game_over = game_over
            current_game_over_msg = game_over_message

        display_turn_and_names(screen, current_turn, player, cpu,
                               player_points=player_points,
                               cpu_points=cpu_points,
                               in_check=current_check)
        draw_board(screen)

        with state_lock:
            draw_pieces(screen, gs)

        if selected_square:
            pg.draw.rect(screen, (0, 255, 0),
                         (BOARD_X + selected_square[1]*SQUARE_SIZE,
                          BOARD_Y + selected_square[0]*SQUARE_SIZE,
                          SQUARE_SIZE, SQUARE_SIZE), 3)

        if current_game_over and current_game_over_msg:
            draw_game_over_overlay(screen, current_game_over_msg)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if current_game_over:
                continue
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                col = (mouse_pos[0] - BOARD_X) // SQUARE_SIZE
                row = (mouse_pos[1] - BOARD_Y) // SQUARE_SIZE

                if row < 0 or row >= DIMENSION or col < 0 or col >= DIMENSION:
                    continue

                with state_lock:
                    piece = gs.board[row][col]
                    ct = turn

                if selected_square is None:
                    if piece != "--" and piece.color == ct:
                        selected_square = (row, col)
                else:
                    start = selected_square
                    end = (row, col)
                    client.send(json.dumps({
                        "type": "move",
                        "data": Move(start, end).to_dict()
                    }).encode())
                    selected_square = None

        pg.display.flip()

    client.close()
    pg.quit()


if __name__ == "__main__":
    run_gui()