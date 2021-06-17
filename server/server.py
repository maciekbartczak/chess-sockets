import logging
import socket
from threading import Thread

import chess
import chess.variant


class Server:
    HOST = '127.0.0.1'
    PORT = 4321
    VARIANTS = {1: 'Standard', 2: 'Atomic', 3: 'Racing Kings'}

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.socket = None
        self.client_white = None
        self.client_black = None
        self.board = None
        self.turn = 'White'
        self.variant = None

    def choose_variant(self):
        for k, v in self.VARIANTS.items():
            print(f'{k}. {v}')
        choice = int(input('Choose variant: '))
        if choice < min(self.VARIANTS.keys()) or choice > max(self.VARIANTS.keys()):
            choice = 1
        self.board = chess.variant.find_variant(self.VARIANTS[choice])()
        self.variant = self.VARIANTS[choice]

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.HOST, self.PORT))
        logging.info(f'Server running at {self.HOST}:{self.PORT}')

    def listen(self):
        self.socket.listen()
        while True:
            sock, addr = self.socket.accept()
            if self.client_white and self.client_black:
                sock.sendall('Server is full'.encode('utf-8'))
                sock.close()
            else:
                if self.client_white is None:
                    self.client_white = sock
                else:
                    self.client_black = sock
                logging.info('New client connected!')
                client = 'White' if sock == self.client_white else 'Black'
                sock.sendall(f'You play as {client}'.encode('utf-8'))
                sock.sendall(f'{self.variant}'.encode('utf-8'))
                sock.sendall(self.board.fen().encode('utf-8'))
                Thread(target=self.on_client_connect, args=(sock, client)).start()

    def on_client_connect(self, socket, client):
        while True:
            try:
                msg = socket.recv(1024).decode('utf-8')
            except Exception:
                break
            logging.info(f'{client} > {msg}')
            try:
                move = chess.Move.from_uci(msg)
            except Exception as e:
                logging.warning(e)
            logging.info(f'current player: {self.turn}')
            if client == self.turn:
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.turn = 'White' if self.turn == 'Black' else 'Black'
                logging.info(f'\n{self.board}')
            if self.client_white is not None:
                self.client_white.sendall(self.board.fen().encode('utf-8'))
            if self.client_black is not None:
                self.client_black.sendall(self.board.fen().encode('utf-8'))
        if socket == self.client_white:
            logging.warning('White closed connection')
            socket.close()
            self.client_white = None
        else:
            logging.warning('Black closed connection')
            socket.close()
            self.client_black = None


def main():
    server = Server()
    server.choose_variant()
    server.start()
    server.listen()


if __name__ == '__main__':
    main()
