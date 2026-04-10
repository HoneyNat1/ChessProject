import socket
import threading
import json
from classes import *
import serial
import time
HOST = "0.0.0.0"
PORT = 5050
isconnected = False
while not isconnected:
    try:
        ser = serial.Serial('COM6', 115200)
        print("Connected")
        isconnected = True
    except serial.SerialException as e:
        print(f"Could not connect")
        ser = None
gantry_movement = False
gs = Game_State()
clients = []
lock = threading.Lock()
turn = "white"
white_score = 0
black_score = 0

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

update_attrs(gs)
def Undo(gs,turn):
    gs.black_pieces.clear()
    gs.white_pieces.clear()

def check_game_over(gs, turn):
    pieces = gs.white_pieces if turn == "white" else gs.black_pieces
    all_valid = []
    for piece in pieces:
        pos = gs.get_pos(piece)
        if pos:
            all_valid.extend(piece.get_valid_moves(pos, gs, turn))

    if not all_valid:
        if gs.if_Check(turn):
            return ("black" if turn == "white" else "white", "checkmate")
        else:
            return (None, "stalemate")
    return None


def broadcast(msg_dict):
    msg = json.dumps(msg_dict).encode()
    dead = []
    with lock:
        for c in clients:
            try:
                c.send(msg)
            except:
                dead.append(c)
        for c in dead:
            clients.remove(c)


def broadcast_state():
    state = gs.to_dict()
    state["turn"] = turn
    state["in_check"] = gs.if_Check(turn) # telling all clients
    broadcast(state)
def handle_client(conn, addr):
    global gs, turn
    print(f"[+] Connected: {addr}")
# sema lock _ append
    with lock:  # clients.send(conn)
        clients.append(conn)
    try:
        # Send currently to states
        initial = gs.to_dict()
        initial["turn"] = turn
        initial["in_check"] = gs.if_Check(turn)
        conn.send(json.dumps(initial).encode())
    except Exception as e:
        print(f"Failed initial send to {addr}: {e}")
        conn.close()
        return

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            try:
                msg = json.loads(data.decode())
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "move":
                move_data = msg.get("data", {})
                start = tuple(move_data.get("start", []))
                end   = tuple(move_data.get("end", []))
                print(start)
                start
                print(end)


                if len(start) != 2 or len(end) != 2:
                    continue

                piece = gs.board[start[0]][start[1]]

                if piece == "--":
                    continue
                if piece.color != turn:
                    print(f"Wrong turn: {piece.color} tried to move on {turn}'s turn")
                    continue

                valid_moves = piece.get_valid_moves(start, gs, piece.color)

                if end in valid_moves:
                    captured = gs.board[end[0]][end[1]]

                    gantry_move(start, end)
                    if captured != "--":
                        captured.captured = True
                    gs.board[end[0]][end[1]] = piece
                    gs.board[start[0]][start[1]] = "--"

                    # Disable castling rights if king or rook moved
                    if isinstance(piece, King):
                        piece.castling = False
                    if isinstance(piece, Castle):
                        piece.castling = False

                    update_attrs(gs)
                    turn = "black" if turn == "white" else "white"
                    broadcast_state()
                    print(f"[Move] {start}->{end} | Next: {turn}")

                    result = check_game_over(gs, turn)
                    if result:
                        winner, reason = result
                        broadcast({"game_over": True, "winner": winner, "reason": reason})
                        print(f"[Game Over] {reason} — winner: {winner}")
                else:
                    print(f"[Invalid] {start}->{end} for {piece.color} {type(piece).__name__}")

            elif msg_type == "start":
                gs = Game_State()
                update_attrs(gs)
                turn = "white"
                broadcast_state()

            elif msg_type == "stop":
                break

    except Exception as e:
        print(f"[Error] {addr}: {e}")
    finally:
        with lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()
        print(f"[-] Disconnected: {addr}")



def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"[Server] Listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down")
    finally:
        s.close()


#ser = serial.Serial("COM6", 115200, timeout=1)
time.sleep(2)  # allow port to open


def gantry_move(start, end):
    ser.write(b"$X\n")

    if start[0]==0:
        xstart = 10
    else:
        xstart=380-47 * start[0]
    if start[1]==0:
        ystart= 10
    else:
       ystart=47 *start[1]

    if end[0]==0:
        xend = 10
    else:
        xend=380-47 * end[0]
    if end[1]==0:
        yend= 10
    else:
       yend=47 *end[1]

#starts
    ser.write(f"G1 X{ystart} Y{xstart} F2000\n".encode())# dupli
    wait_until_idle(ser)
    print("Gantry has stopped")
#endpoint
    ser.write(f"G1 X{yend} Y{xend} F2000\n".encode())  # move to X.. Y ..
def wait_until_idle(ser, poll_interval=0.3):
    while True: # time.sleep(0.2)
        ser.write(b"?\n")
        status = ser.readline().decode().strip()
        print(f"Status: {status}")
        if "<Idle" in status: # looks for <Idle|MPos
            break
        time.sleep(poll_interval)
        ser.write(b"$X\n")
if __name__ == "__main__":
    run_server()