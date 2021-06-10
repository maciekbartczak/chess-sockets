import socket
from threading import Thread
import chess
import pygame as pg
import sys

HOST = '127.0.0.1'
PORT = 4321
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (142, 142, 142)
LIGHT = (252, 204, 116)
DARK = (87, 58, 46)
GREEN = (0, 255, 0)
SQUARE_SIZE = 100

pieces_names = {'r': 'blackRook', 'n': 'blackKnight', 'b': 'blackBishop', 'q': 'blackQueen', 'k': 'blackKing',
          'p': 'blackPawn',
          'R': 'whiteRook', 'N': 'whiteKnight', 'B': 'whiteBishop', 'Q': 'whiteQueen', 'K': 'whiteKing',
          'P': 'whitePawn'}

def load_pieces_imgs():
    piece_img = dict()
    for k, v in pieces_names.items():
        print(f'loading ./pieces/{v}.png for {k}')
        img = pg.image.load(f'./pieces/{v}.png')
        img = pg.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
        piece_img[k] = img
    return piece_img

piece_img = load_pieces_imgs()


def receive_board_update():
    global board
    while True:
        board_fen = socket.recv(1024).decode('utf-8')
        board = chess.Board(board_fen)
        if 'Black' in welcome_message:
            board = board.transform(chess.flip_vertical)
        print(f'\n{board}')
        screen.fill(GREY)
        draw_board(screen)
        draw_pieces(screen)
        pg.display.update()


def send_move(src_x, src_y, dst_x, dst_y):
    print(src_x, src_y, dst_x, dst_y)
    reversed_y = {7 : 1, 6 : 2, 5 : 3, 4 : 4, 3 : 5, 2 : 6, 1 : 7, 0 : 8}
    if 'Black' in welcome_message:
        src = f'{convert(src_x)}{src_y + 1}{convert(dst_x)}{dst_y + 1}'
    else:
        src = f'{convert(src_x)}{reversed_y[src_y]}{convert(dst_x)}{reversed_y[dst_y]}'
    print('sending ' + src)
    socket.send(src.encode('utf-8'))


def draw_board(screen):
    light = False
    for i in range(8):
        for j in range(8):
            pg.draw.rect(screen, LIGHT if light else DARK,
                         ((j * SQUARE_SIZE), (i * SQUARE_SIZE), SQUARE_SIZE, SQUARE_SIZE))
            light = not light
        light = not light


def draw_pieces(screen):
    fen = board.fen()
    pieces = fen.split(' ')[0]
    for i, row in enumerate(pieces.split('/')):
        j = 0
        file = 0
        while file < 8 and j < row.__len__():
            if row[j] not in pieces_names:
                file += int(row[j]) - 1
            else:
                screen.blit(piece_img[row[j]], (file * SQUARE_SIZE, i * SQUARE_SIZE))
            j += 1
            file += 1


def mouse_to_board(x, y):
    board_x = int(x / SQUARE_SIZE)
    board_y = int(y / SQUARE_SIZE)
    return board_x, board_y

def convert(n):
    if n == 0:
        return 'a'
    elif n == 1:
        return 'b'
    elif n == 2:
        return 'c'
    elif n == 3:
        return 'd'
    elif n == 4:
        return 'e'
    elif n == 5:
        return 'f'
    elif n == 6:
        return 'g'
    elif n == 7:
        return 'h'

board = chess.Board()
pg.init()
pg.display.set_caption('Chess')
screen = pg.display.set_mode((800, 800))

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((HOST, PORT))
welcome_message = socket.recv(1024).decode('utf-8')
if 'Black' in welcome_message:
    board = board.transform(chess.flip_vertical)
print(welcome_message)
Thread(target=receive_board_update).start()


piece_selected = False
source_x, source_y = -1, -1

while True:
    screen.fill(WHITE)
    draw_board(screen)
    draw_pieces(screen)
    for event in pg.event.get():
        if event.type == pg.MOUSEBUTTONDOWN:
            if not piece_selected:
                piece_selected = True
                x, y = pg.mouse.get_pos()
                source_x, source_y = mouse_to_board(x, y)
            else:
                x, y = pg.mouse.get_pos()
                dest_x, dest_y = mouse_to_board(x, y)
                send_move(source_x, source_y, dest_x, dest_y)
                piece_selected = False
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()
    if piece_selected:
        pg.draw.circle(screen, GREEN, (source_x * SQUARE_SIZE + (SQUARE_SIZE / 2), source_y * SQUARE_SIZE + (SQUARE_SIZE / 2)), SQUARE_SIZE / 2, 5)
    pg.display.update()
