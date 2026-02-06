import socket
import threading
import json
import time
import sys
import os
from datetime import datetime


class ChessClient:
    def __init__(self, server_host='localhost', server_port=5555):
        self.server_host = server_host
        self.server_port = server_port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.username = None
        self.room_id = None
        self.color = None
        self.opponent = None
        self.board_state = None
        self.game_started = False
        self.game_over = False

        # Для отображения доски (упрощенная версия)
        self.piece_symbols = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
            '.': '·'
        }

    def connect(self):
        """Подключение к серверу"""
        try:
            self.client.connect((self.server_host, self.server_port))
            print(f"[CLIENT] Подключено к серверу {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"[CLIENT] Ошибка подключения: {e}")
            return False

    def send(self, data):
        """Отправить данные на сервер"""
        try:
            self.client.send(json.dumps(data).encode('utf-8'))
        except Exception as e:
            print(f"[CLIENT] Ошибка отправки: {e}")

    def receive(self):
        """Получение сообщений от сервера"""
        while True:
            try:
                data = self.client.recv(4096)
                if not data:
                    print("[CLIENT] Соединение с сервером разорвано")
                    os._exit(1)

                message = json.loads(data.decode('utf-8'))
                self.handle_message(message)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"[CLIENT] Ошибка получения: {e}")
                break

    def handle_message(self, message):
        """Обработка сообщений от сервера"""
        msg_type = message.get('type')

        if msg_type == 'rooms_list':
            print("\n" + "=" * 50)
            print("ДОСТУПНЫЕ КОМНАТЫ:")
            print("=" * 50)

            rooms = message.get('rooms', [])
            if not rooms:
                print("Нет доступных комнат. Создайте новую!")
            else:
                for i, room in enumerate(rooms, 1):
                    players = ", ".join(room['players'])
                    print(f"{i}. Комната {room['room_id']}: {players}")
            print("=" * 50)

            self.show_main_menu()

        elif msg_type == 'room_created':
            self.room_id = message.get('room_id')
            self.color = message.get('color')
            print(f"\n✓ Комната создана: {self.room_id}")
            print(f"✓ Вы играете белыми")
            print("✓ Ожидаем второго игрока...")
            print("Введите 'chat [сообщение]' для отправки сообщения")

        elif msg_type == 'player_joined':
            self.opponent = message.get('opponent')
            print(f"\n✓ {self.opponent} присоединился к игре!")
            print(f"✓ Он играет {message.get('color')}")
            self.game_started = True

        elif msg_type == 'room_joined':
            self.room_id = message.get('room_id')
            self.color = message.get('color')
            self.board_state = message.get('board_state')
            self.opponent = message.get('opponent')
            self.game_started = True

            print(f"\n✓ Вы присоединились к комнате {self.room_id}")
            print(f"✓ Вы играете черными")
            print(f"✓ Ваш соперник: {self.opponent}")

            self.print_board()

            if message.get('your_turn'):
                print("\n✓ Сейчас ваш ход!")
            else:
                print("\n✗ Ход противника. Ожидайте...")

        elif msg_type == 'game_started':
            white = message.get('white')
            black = message.get('black')
            print(f"\n" + "=" * 50)
            print(f"ИГРА НАЧАЛАСЬ!")
            print(f"Белые: {white}")
            print(f"Черные: {black}")
            print("=" * 50)
            self.print_board()
            if self.color == 'white':
                print("\n✓ Ваш ход первый!")
            else:
                print("\n✗ Ход противника. Ожидайте...")

        elif msg_type == 'move_made':
            player = message.get('player')
            move_san = message.get('move_san')
            self.board_state = message.get('board_state')

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {player}: {move_san}")

            if player == self.username:
                print("✓ Ход принят сервером")
            else:
                print(f"✓ {player} сделал ход")

            self.print_board()

            if message.get('game_over'):
                result = message.get('result')
                print("\n" + "=" * 50)
                print("ИГРА ОКОНЧЕНА!")
                print(f"Результат: {result}")
                print("=" * 50)
                self.game_over = True
                self.show_game_over_menu()
            else:
                next_turn = message.get('next_turn')
                if next_turn == self.color:
                    print("\n✓ Ваш ход!")
                else:
                    print("\n✗ Ход противника. Ожидайте...")

        elif msg_type == 'board_state':
            self.board_state = message.get('board_state')
            self.print_board()

            if message.get('your_turn'):
                print("\n✓ Ваш ход!")
            else:
                print("\n✗ Ход противника. Ожидайте...")

        elif msg_type == 'chat_message':
            sender = message.get('sender')
            text = message.get('text')
            timestamp = message.get('timestamp')
            print(f"\n[{timestamp}] {sender}: {text}")

        elif msg_type == 'player_left':
            player = message.get('player')
            print(f"\n⚠ {player} покинул игру")
            self.game_over = True

        elif msg_type == 'player_disconnected':
            player = message.get('player')
            print(f"\n⚠ {player} отключился от игры")
            self.game_over = True

        elif msg_type == 'game_over':
            result = message.get('result')
            reason = message.get('reason')
            winner = message.get('winner')

            print("\n" + "=" * 50)
            print("ИГРА ОКОНЧЕНА!")
            print(f"Результат: {result}")
            print(f"Причина: {reason}")
            if winner:
                print(f"Победитель: {'Белые' if winner == 'white' else 'Черные'}")
            print("=" * 50)

            self.game_over = True
            self.show_game_over_menu()

        elif msg_type == 'error':
            print(f"\n✗ Ошибка: {message.get('message')}")

    def print_board(self):
        """Отображение шахматной доски"""
        if not self.board_state:
            return

        # Парсим FEN
        fen = self.board_state['fen']
        board_part = fen.split(' ')[0]

        # Преобразуем FEN в матрицу
        board = []
        for row in board_part.split('/'):
            board_row = []
            for char in row:
                if char.isdigit():
                    board_row.extend(['.' for _ in range(int(char))])
                else:
                    board_row.append(char)
            board.append(board_row)

        print("\n    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")

        for i, row in enumerate(board):
            print(f"{8 - i} |", end="")
            for piece in row:
                symbol = self.piece_symbols.get(piece, piece)
                print(f" {symbol} |", end="")
            print(f" {8 - i}")
            print("  +---+---+---+---+---+---+---+---+")

        print("    a   b   c   d   e   f   g   h")

        # Дополнительная информация
        if self.board_state['is_check']:
            print("\n⚠ ШАХ!")
        if self.board_state['is_checkmate']:
            print("\n⚠ МАТ!")
        if self.board_state['is_stalemate']:
            print("\n⚠ ПАТ!")

    def show_main_menu(self):
        """Главное меню"""
        print("\n" + "=" * 50)
        print("ГЛАВНОЕ МЕНЮ")
        print("=" * 50)
        print("1. Создать комнату")
        print("2. Присоединиться к комнате")
        print("3. Обновить список комнат")
        print("4. Выйти")
        print("=" * 50)

        choice = input("Выберите действие: ").strip()

        if choice == '1':
            self.send({
                'type': 'create_room',
                'username': self.username
            })
        elif choice == '2':
            room_id = input("Введите ID комнаты: ").strip()
            self.send({
                'type': 'join_room',
                'room_id': room_id,
                'username': self.username
            })
        elif choice == '3':
            self.send({
                'type': 'get_rooms',
                'username': self.username
            })
        elif choice == '4':
            print("Выход...")
            self.client.close()
            os._exit(0)
        else:
            print("Неверный выбор!")
            self.show_main_menu()

    def show_game_over_menu(self):
        """Меню после окончания игры"""
        print("\n" + "=" * 50)
        print("МЕНЮ ПОСЛЕ ИГРЫ")
        print("=" * 50)
        print("1. Вернуться в главное меню")
        print("2. Сыграть реванш")
        print("3. Выйти")
        print("=" * 50)

        choice = input("Выберите действие: ").strip()

        if choice == '1':
            self.room_id = None
            self.color = None
            self.opponent = None
            self.board_state = None
            self.game_started = False
            self.game_over = False
            self.send({
                'type': 'get_rooms',
                'username': self.username
            })
        elif choice == '2':
            print("Реванш пока не реализован. Возврат в главное меню...")
            self.room_id = None
            self.color = None
            self.opponent = None
            self.board_state = None
            self.game_started = False
            self.game_over = False
            self.send({
                'type': 'get_rooms',
                'username': self.username
            })
        elif choice == '3':
            print("Выход...")
            self.client.close()
            os._exit(0)
        else:
            print("Неверный выбор!")
            self.show_game_over_menu()

    def game_loop(self):
        """Основной игровой цикл"""
        while True:
            try:
                if not self.game_started or self.game_over:
                    time.sleep(0.1)
                    continue

                # Получаем команду от пользователя
                cmd = input("\nВведите ход или команду: ").strip()

                if cmd.lower() in ['exit', 'quit', 'выход']:
                    if self.room_id:
                        self.send({
                            'type': 'leave_room',
                            'room_id': self.room_id
                        })
                    self.client.close()
                    break

                elif cmd.lower() in ['board', 'доска']:
                    self.send({
                        'type': 'get_board',
                        'room_id': self.room_id,
                        'color': self.color
                    })

                elif cmd.startswith('chat '):
                    text = cmd[5:]
                    self.send({
                        'type': 'chat',
                        'room_id': self.room_id,
                        'text': text
                    })

                elif cmd.lower() in ['help', 'помощь', '?']:
                    print("\n" + "=" * 50)
                    print("КОМАНДЫ:")
                    print("=" * 50)
                    print("Ходы в формате: e2e4, e7e5, g1f3 и т.д.")
                    print("chat [сообщение] - отправить сообщение")
                    print("board - обновить доску")
                    print("resign - сдаться")
                    print("exit - выйти из игры")
                    print("=" * 50)

                elif cmd.lower() == 'resign':
                    confirm = input("Вы уверены, что хотите сдаться? (да/нет): ").lower()
                    if confirm in ['да', 'yes', 'y', 'д']:
                        self.send({
                            'type': 'resign',
                            'room_id': self.room_id,
                            'color': self.color
                        })

                elif len(cmd) >= 4:  # Предполагаем, что это ход
                    self.send({
                        'type': 'move',
                        'room_id': self.room_id,
                        'move': cmd,
                        'color': self.color,
                        'username': self.username
                    })

                else:
                    print("Неверная команда. Введите 'help' для списка команд")

            except KeyboardInterrupt:
                print("\nВыход...")
                if self.room_id:
                    self.send({
                        'type': 'leave_room',
                        'room_id': self.room_id
                    })
                self.client.close()
                break
            except Exception as e:
                print(f"Ошибка: {e}")

    def start(self):
        """Запуск клиента"""
        print("=" * 50)
        print("ШАХМАТНЫЙ КЛИЕНТ")
        print("=" * 50)

        # Ввод имени пользователя
        self.username = input("Введите ваше имя: ").strip()
        if not self.username:
            self.username = f"Игрок_{int(time.time()) % 1000}"

        # Подключение к серверу
        if not self.connect():
            return

        # Отправка имени пользователя
        self.send({
            'type': 'connect',
            'username': self.username
        })

        # Запуск потока для получения сообщений
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()

        # Ожидаем список комнат
        time.sleep(1)

        # Запуск игрового цикла
        self.game_loop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Шахматный клиент')
    parser.add_argument('--host', default='localhost', help='Адрес сервера')
    parser.add_argument('--port', type=int, default=5555, help='Порт сервера')

    args = parser.parse_args()

    client = ChessClient(server_host=args.host, server_port=args.port)
    client.start()