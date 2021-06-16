import socket
from threading import Thread
import chess
import pygame as pg
import sys


class Client:
    HOST = '127.0.0.1'
    PORT = 4321
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREY = (142, 142, 142)
    LIGHT = (252, 204, 116)
    DARK = (87, 58, 46)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    VALID_DARK = (76, 153, 0)
    VALID_LIGHT = (102, 204, 0)
    SQUARE_SIZE = 100
    PIECE_NAMES = {'r': 'blackRook', 'n': 'blackKnight', 'b': 'blackBishop', 'q': 'blackQueen', 'k': 'blackKing',
                   'p': 'blackPawn',
                   'R': 'whiteRook', 'N': 'whiteKnight', 'B': 'whiteBishop', 'Q': 'whiteQueen', 'K': 'whiteKing',
                   'P': 'whitePawn'}

    def __init__(self):
        self.color = None
        self.board = chess.Board()
        self.screen = None
        self.piece_imgs = self.load_pieces_imgs()
        self.welcome_message = ''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.piece_selected = False
        self.selected_x = -1
        self.selected_y = -1
        self.target_x = -1
        self.target_y = -1
        self.moves = []

    def load_pieces_imgs(self):
        piece_img = dict()
        for k, v in self.PIECE_NAMES.items():
            print(f'loading ./pieces/{v}.png for {k}')
            img = pg.image.load(f'./pieces/{v}.png')
            img = pg.transform.scale(img, (self.SQUARE_SIZE, self.SQUARE_SIZE))
            piece_img[k] = img
        return piece_img

    def receive_board_update(self):
        global board
        while True:
            board_fen = self.socket.recv(1024).decode('utf-8')
            self.board = chess.Board(board_fen)
            print(f'\n{self.board}')
            self.screen.fill(self.GREY)
            self.draw_board(self.screen)
            self.draw_pieces(self.screen)
            pg.display.update()

    def send_move(self, src_x, src_y, dst_x, dst_y):
        print(src_x, src_y, dst_x, dst_y)
        src = f'{self.x_to_name(src_x)}{self.reverse_y(src_y)}{self.x_to_name(dst_x)}{self.reverse_y(dst_y)}'
        print('sending ' + src)
        self.socket.send(src.encode('utf-8'))

    @staticmethod
    def reverse_y(y):
        reversed_y = {7: 1, 6: 2, 5: 3, 4: 4, 3: 5, 2: 6, 1: 7, 0: 8}
        return reversed_y[y]

    def draw_board(self, screen):
        light = False
        for i in range(8):
            for j in range(8):
                pg.draw.rect(screen, self.LIGHT if light else self.DARK,
                             ((j * self.SQUARE_SIZE), (i * self.SQUARE_SIZE), self.SQUARE_SIZE, self.SQUARE_SIZE))
                light = not light
            light = not light

    def draw_pieces(self, screen):
        fen = self.board.fen()
        pieces = fen.split(' ')[0]
        for i, row in enumerate(pieces.split('/')):
            j = 0
            file = 0
            while file < 8 and j < row.__len__():
                if row[j] not in self.PIECE_NAMES:
                    file += int(row[j]) - 1
                else:
                    screen.blit(self.piece_imgs[row[j]], (file * self.SQUARE_SIZE, i * self.SQUARE_SIZE))
                j += 1
                file += 1

    def mouse_to_board(self, x, y):
        board_x = int(x / self.SQUARE_SIZE)
        board_y = int(y / self.SQUARE_SIZE)
        return board_x, board_y

    def board_to_square(self, x, y):
        return chess.square(x, self.reverse_y(y) - 1)

    @staticmethod
    def x_to_name(n):
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

    def generate_moves(self):
        self.moves.clear()
        for square in chess.SQUARES:
            try:
                move = self.board.find_move(self.board_to_square(self.selected_x, self.selected_y), square)
                print(move)
                self.moves.append(move)
            except Exception as e:
                pass

    def run(self):
        pg.init()
        pg.display.set_caption('Chess')
        self.screen = pg.display.set_mode((800, 800))
        self.socket.connect((self.HOST, self.PORT))
        self.welcome_message = self.socket.recv(1024).decode('utf-8')
        self.color = chess.BLACK if 'Black' in self.welcome_message else chess.WHITE
        print(self.welcome_message)
        Thread(target=self.receive_board_update).start()
        while True:
            self.screen.fill(self.WHITE)
            self.draw_board(self.screen)
            self.draw_pieces(self.screen)
            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONDOWN:
                    x, y = pg.mouse.get_pos()
                    xx, yy = self.mouse_to_board(x, y)
                    source_sq = self.board_to_square(xx, yy)
                    source_piece = self.board.piece_at(source_sq)
                    if source_piece is not None and source_piece.color == self.color and not self.piece_selected:
                        self.piece_selected = True
                        self.selected_x, self.selected_y = self.mouse_to_board(x, y)
                        self.generate_moves()
                    elif self.piece_selected:
                        self.target_x, self.target_y = self.mouse_to_board(x, y)
                        if not (self.selected_x == self.target_x and self.selected_y == self.target_y):
                            target_sq = self.board_to_square(self.target_x, self.target_y)
                            target_piece = self.board.piece_at(target_sq)
                            if target_piece is not None and target_piece.color == self.color:
                                self.selected_x, self.selected_y = self.target_x, self.target_y
                                self.generate_moves()
                            else:
                                self.send_move(self.selected_x, self.selected_y, self.target_x, self.target_y)
                                self.piece_selected = False
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            if self.piece_selected:
                pg.draw.circle(self.screen, self.GREEN,
                               (self.selected_x * self.SQUARE_SIZE + (self.SQUARE_SIZE / 2),
                                self.selected_y * self.SQUARE_SIZE + (self.SQUARE_SIZE / 2)),
                               self.SQUARE_SIZE / 2, 5)
                for move in self.moves:
                    target = str(move)[-2:]
                    try:
                        target_sq = chess.parse_square(target)
                        pg.draw.rect(self.screen, self.VALID_LIGHT if (chess.square_file(target_sq) + chess.square_rank(target_sq)) % 2 == 0 else self.VALID_DARK,
                                     ((chess.square_file(target_sq) * self.SQUARE_SIZE),
                                      ((self.reverse_y(chess.square_rank(target_sq)) - 1) * self.SQUARE_SIZE),
                                      self.SQUARE_SIZE, self.SQUARE_SIZE))
                    except Exception:
                        pass

            if self.board.is_checkmate():
                if self.board.turn == chess.BLACK:
                    print("Black got checkmated")
                else:
                    print("White got checkmated")
                pg.quit()
                sys.exit()

            if self.board.is_stalemate():
                print("Stalemate")
                pg.quit()
                sys.exit()

            if self.board.is_insufficient_material():
                print("Insufficient Material")
                pg.quit()
                sys.exit()

            if self.board.is_check():
                if self.board.turn == chess.WHITE:
                    king = self.board.king(chess.WHITE)
                else:
                    king = self.board.king(chess.BLACK)
                pg.draw.rect(self.screen, self.RED,
                             ((chess.square_file(king) * self.SQUARE_SIZE),
                              ((self.reverse_y(chess.square_rank(king)) - 1) * self.SQUARE_SIZE),
                              self.SQUARE_SIZE, self.SQUARE_SIZE))
            pg.display.update()


def main():
    client = Client()
    client.run()


if __name__ == '__main__':
    main()
