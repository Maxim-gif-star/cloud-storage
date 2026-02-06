import chess
import chess.pgn
from datetime import datetime
import socket
import json
import threading


class ChessMultiplayer(Chess_OOP):  # Наследуем от вашего класса
    def __init__(self, mode='local'):
        super().__init__()
        self.mode = mode  # 'local' или 'network'
        self.socket = None
        self.room_id = None
        self.color = None
        self.opponent = None
        self.network_thread = None
        self.game_started = False

        if mode == 'network':
            self.setup_network()

    def setup_network(self):
        """Настройка сетевого подключения"""
        print("\n" + "=" * 50)
        print("СЕТЕВОЙ РЕЖИМ")
        print("=" * 50)

        while True:
            try:
                choice = input("Вы хотите:\n1. Создать сервер\n2. Подключиться к серверу\nВыбор: ").strip()

                if choice == '1':
                    self.start_server()
                    break
                elif choice == '2':
                    self.connect_to_server()
                    break
                else:
                    print("Неверный выбор!")

            except KeyboardInterrupt:
                print("\nВозврат в главное меню...")
                return

    def start_server(self):
        """Запуск сервера на локальной машине"""
        import subprocess
        import sys

        print("\nЗапуск сервера...")

        # Запускаем сервер в отдельном процессе
        server_process = subprocess.Popen(
            [sys.executable, "chess_server.py", "--host", "localhost", "--port", "5555"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Даем серверу время запуститься
        import time
        time.sleep(2)

        print("Сервер запущен. Теперь запустите клиент в другом окне.")
        print("Нажмите Enter для запуска клиента...")
        input()

        # Запускаем клиент
        self.connect_to_server('localhost')

    def connect_to_server(self, host=None):
        """Подключение к серверу"""
        if not host:
            host = input("Введите адрес сервера (например: localhost или IP): ").strip()

        port = 5555

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))

            print(f"Подключено к серверу {host}:{port}")

            # Получаем имя игрока
            username = input("Введите ваше имя: ").strip()
            if not username:
                username = f"Игрок_{id(self) % 1000}"

            # Отправляем имя
            self.socket.send(json.dumps({
                'username': username
            }).encode('utf-8'))

            # Запускаем поток для получения сообщений
            self.network_thread = threading.Thread(target=self.receive_messages)
            self.network_thread.daemon = True
            self.network_thread.start()

            # Основной игровой цикл будет в game()

        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return

    def receive_messages(self):
        """Получение сообщений от сервера"""
        while True:
            try:
                data = self.socket.recv(4096)
                if not data:
                    print("Соединение с сервером разорвано")
                    break

                message = json.loads(data.decode('utf-8'))
                self.handle_network_message(message)

            except Exception as e:
                print(f"Ошибка получения: {e}")
                break

    def handle_network_message(self, message):
        """Обработка сетевых сообщений"""
        msg_type = message.get('type')

        if msg_type == 'rooms_list':
            self.show_rooms(message.get('rooms', []))

        elif msg_type == 'room_created':
            self.room_id = message.get('room_id')
            self.color = 'white'
            print(f"Комната создана: {self.room_id}")
            print("Ожидаем второго игрока...")

        elif msg_type == 'player_joined':
            self.opponent = message.get('opponent')
            print(f"{self.opponent} присоединился!")
            self.game_started = True

        elif msg_type == 'room_joined':
            self.room_id = message.get('room_id')
            self.color = 'black'
            self.opponent = message.get('opponent')
            self.game_started = True

            # Обновляем доску
            board_state = message.get('board_state')
            if board_state:
                self.board = chess.Board(board_state['fen'])
                self.print_board()

        elif msg_type == 'move_made':
            move_uci = message.get('move')
            move_san = message.get('move_san')

            # Применяем ход к нашей доске
            move = chess.Move.from_uci(move_uci)
            self.board.push(move)

            print(f"\nХод противника: {move_san}")
            self.print_board()

            if message.get('game_over'):
                print(f"Игра окончена! Результат: {message.get('result')}")
                self.game_started = False

    def show_rooms(self, rooms):
        """Показать список комнат"""
        print("\nДоступные комнаты:")
        for i, room in enumerate(rooms, 1):
            players = ", ".join(room['players'])
            print(f"{i}. {room['room_id']} - {players}")

        print("\nВыберите действие:")
        print("1. Создать комнату")
        print("2. Присоединиться к комнате")
        print("3. Обновить список")

        choice = input("Ваш выбор: ").strip()

        if choice == '1':
            self.socket.send(json.dumps({
                'type': 'create_room'
            }).encode('utf-8'))
        elif choice == '2':
            room_id = input("Введите ID комнаты: ").strip()
            self.socket.send(json.dumps({
                'type': 'join_room',
                'room_id': room_id
            }).encode('utf-8'))
        elif choice == '3':
            # Запрос обновленного списка
            pass

    def get_move_input_network(self):
        """Получение хода в сетевом режиме"""
        while self.game_started:
            try:
                move_input = input(f"Ваш ход ({self.color}): ").strip()

                if move_input == 'exit':
                    break

                # Пробуем отправить ход
                move = chess.Move.from_uci(move_input)
                if move in self.board.legal_moves:
                    self.socket.send(json.dumps({
                        'type': 'move',
                        'room_id': self.room_id,
                        'move': move_input,
                        'color': self.color
                    }).encode('utf-8'))

                    # Применяем ход локально
                    self.board.push(move)
                    self.print_board()
                    return
                else:
                    print("Неверный ход!")

            except Exception as e:
                print(f"Ошибка: {e}")

    def game(self):
        """Основная игровая функция с поддержкой сети"""
        if self.mode == 'local':
            # Используем оригинальную логику
            super().game()
        else:
            # Сетевая игра
            print("Сетевой режим активирован")

            while not self.game_started:
                import time
                time.sleep(0.1)

            # Игровой цикл
            while self.game_started:
                if self.board.turn == (chess.WHITE if self.color == 'white' else chess.BLACK):
                    # Наш ход
                    self.get_move_input_network()
                else:
                    # Ход противника - ждем
                    print("Ход противника. Ожидайте...")
                    import time
                    time.sleep(1)

                # Проверяем окончание игры
                if self.handle_game_over():
                    break


if __name__ == "__main__":
    print("Выберите режим игры:")
    print("1. Локальная игра (два игрока на одном компьютере)")
    print("2. Сетевая игра")

    choice = input("Ваш выбор (1 или 2): ").strip()

    if choice == '1':
        chess_game = Chess_OOP()
        chess_game.game()
    elif choice == '2':
        chess_game = ChessMultiplayer(mode='network')
        chess_game.game()
    else:
        print("Неверный выбор!")