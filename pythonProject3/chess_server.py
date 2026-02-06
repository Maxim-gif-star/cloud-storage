import socket
import threading
import json
import chess
import sys
from datetime import datetime


class ChessServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))

        self.clients = []
        self.usernames = {}
        self.rooms = {}
        self.room_counters = {}

        print(f"[SERVER] Сервер запущен на {host}:{port}")

    def broadcast_to_room(self, room_id, message, exclude_client=None):
        """Отправить сообщение всем в комнате"""
        if room_id in self.rooms:
            for client in self.rooms[room_id]:
                if client != exclude_client:
                    try:
                        client.send(json.dumps(message).encode('utf-8'))
                    except:
                        pass

    def handle_client(self, client, address):
        """Обработка подключения клиента"""
        print(f"[SERVER] Новое подключение от {address}")

        try:
            # Получаем имя пользователя
            username_data = json.loads(client.recv(1024).decode('utf-8'))
            username = username_data.get('username', f'Игрок_{address[1]}')
            self.usernames[client] = username

            # Отправляем список комнат
            rooms_info = []
            for room_id, clients in self.rooms.items():
                if len(clients) < 2:  # Комната не заполнена
                    player = self.usernames[clients[0]] if clients else "Ожидание"
                    rooms_info.append({
                        'room_id': room_id,
                        'players': [player],
                        'status': 'waiting'
                    })

            client.send(json.dumps({
                'type': 'rooms_list',
                'rooms': rooms_info
            }).encode('utf-8'))

            while True:
                try:
                    data = client.recv(4096)
                    if not data:
                        break

                    message = json.loads(data.decode('utf-8'))
                    msg_type = message.get('type')

                    if msg_type == 'create_room':
                        room_id = f"room_{len(self.rooms) + 1}"
                        self.rooms[room_id] = [client]
                        self.room_counters[room_id] = {
                            'board': chess.Board(),
                            'move_history': [],
                            'players': {0: client},  # Белые - 0
                            'current_turn': chess.WHITE,
                            'game_over': False
                        }

                        response = {
                            'type': 'room_created',
                            'room_id': room_id,
                            'color': 'white',
                            'username': username
                        }
                        client.send(json.dumps(response).encode('utf-8'))

                        print(f"[SERVER] Комната {room_id} создана пользователем {username}")

                    elif msg_type == 'join_room':
                        room_id = message.get('room_id')

                        if room_id in self.rooms and len(self.rooms[room_id]) < 2:
                            self.rooms[room_id].append(client)
                            room_data = self.room_counters[room_id]
                            room_data['players'][1] = client  # Черные - 1

                            # Уведомляем создателя комнаты
                            room_creator = room_data['players'][0]
                            room_creator.send(json.dumps({
                                'type': 'player_joined',
                                'opponent': username,
                                'color': 'black'
                            }).encode('utf-8'))

                            # Отправляем данные второму игроку
                            board_state = self.get_board_state(room_data['board'])
                            response = {
                                'type': 'room_joined',
                                'room_id': room_id,
                                'color': 'black',
                                'board_state': board_state,
                                'opponent': self.usernames.get(room_creator, 'Игрок 1'),
                                'your_turn': False
                            }
                            client.send(json.dumps(response).encode('utf-8'))

                            # Уведомляем обоих игроков о начале игры
                            self.broadcast_to_room(room_id, {
                                'type': 'game_started',
                                'white': self.usernames.get(room_data['players'][0]),
                                'black': username
                            })

                            print(f"[SERVER] {username} присоединился к комнате {room_id}")
                        else:
                            client.send(json.dumps({
                                'type': 'error',
                                'message': 'Комната заполнена или не существует'
                            }).encode('utf-8'))

                    elif msg_type == 'move':
                        room_id = message.get('room_id')
                        move_uci = message.get('move')
                        player_color = message.get('color')

                        if room_id in self.room_counters:
                            room_data = self.room_counters[room_id]

                            # Проверяем, чей сейчас ход
                            expected_color = 'white' if room_data['current_turn'] == chess.WHITE else 'black'
                            if player_color != expected_color:
                                client.send(json.dumps({
                                    'type': 'error',
                                    'message': 'Сейчас не ваш ход!'
                                }).encode('utf-8'))
                                continue

                            # Пробуем сделать ход
                            try:
                                move = chess.Move.from_uci(move_uci)
                                if move in room_data['board'].legal_moves:
                                    room_data['board'].push(move)
                                    room_data['move_history'].append(move_uci)

                                    # Меняем очередь хода
                                    room_data['current_turn'] = not room_data['current_turn']

                                    # Получаем состояние доски
                                    board_state = self.get_board_state(room_data['board'])
                                    move_san = room_data['board'].san(move)

                                    # Проверяем окончание игры
                                    game_over = room_data['board'].is_game_over()
                                    result = room_data['board'].result() if game_over else '*'

                                    if game_over:
                                        room_data['game_over'] = True

                                    # Отправляем ход всем игрокам в комнате
                                    self.broadcast_to_room(room_id, {
                                        'type': 'move_made',
                                        'move': move_uci,
                                        'move_san': move_san,
                                        'board_state': board_state,
                                        'next_turn': 'white' if room_data['current_turn'] == chess.WHITE else 'black',
                                        'game_over': game_over,
                                        'result': result,
                                        'player': username
                                    })

                                    print(f"[SERVER] {username} сделал ход {move_san} в комнате {room_id}")
                                else:
                                    client.send(json.dumps({
                                        'type': 'error',
                                        'message': 'Неверный ход!'
                                    }).encode('utf-8'))
                            except Exception as e:
                                client.send(json.dumps({
                                    'type': 'error',
                                    'message': f'Ошибка хода: {str(e)}'
                                }).encode('utf-8'))

                    elif msg_type == 'get_board':
                        room_id = message.get('room_id')
                        if room_id in self.room_counters:
                            room_data = self.room_counters[room_id]
                            board_state = self.get_board_state(room_data['board'])
                            client.send(json.dumps({
                                'type': 'board_state',
                                'board_state': board_state,
                                'your_turn': ('white' if room_data[
                                                             'current_turn'] == chess.WHITE else 'black') == message.get(
                                    'color'),
                                'game_over': room_data['game_over']
                            }).encode('utf-8'))

                    elif msg_type == 'chat':
                        room_id = message.get('room_id')
                        text = message.get('text')
                        self.broadcast_to_room(room_id, {
                            'type': 'chat_message',
                            'sender': username,
                            'text': text,
                            'timestamp': datetime.now().strftime("%H:%M")
                        }, exclude_client=client)

                    elif msg_type == 'resign':
                        room_id = message.get('room_id')
                        if room_id in self.room_counters:
                            winner = 'black' if message.get('color') == 'white' else 'white'
                            self.broadcast_to_room(room_id, {
                                'type': 'game_over',
                                'result': f'1-0' if winner == 'white' else '0-1',
                                'reason': f'{username} сдался',
                                'winner': winner
                            })
                            # Удаляем комнату после окончания игры
                            if room_id in self.rooms:
                                del self.rooms[room_id]
                            if room_id in self.room_counters:
                                del self.room_counters[room_id]

                    elif msg_type == 'leave_room':
                        room_id = message.get('room_id')
                        if room_id in self.rooms:
                            if client in self.rooms[room_id]:
                                self.rooms[room_id].remove(client)
                                # Уведомляем другого игрока
                                self.broadcast_to_room(room_id, {
                                    'type': 'player_left',
                                    'player': username
                                })
                                # Если в комнате никого не осталось, удаляем её
                                if not self.rooms[room_id]:
                                    del self.rooms[room_id]
                                    if room_id in self.room_counters:
                                        del self.room_counters[room_id]

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"[SERVER] Ошибка обработки данных: {e}")
                    break

        except Exception as e:
            print(f"[SERVER] Ошибка клиента {address}: {e}")
        finally:
            # Удаляем клиента из всех комнат
            for room_id, clients in list(self.rooms.items()):
                if client in clients:
                    clients.remove(client)
                    # Уведомляем другого игрока
                    opponent = next((c for c in clients if c != client), None)
                    if opponent:
                        try:
                            opponent.send(json.dumps({
                                'type': 'player_disconnected',
                                'player': self.usernames.get(client, 'Игрок')
                            }).encode('utf-8'))
                        except:
                            pass

                    # Если в комнате никого не осталось, удаляем её
                    if not clients:
                        del self.rooms[room_id]
                        if room_id in self.room_counters:
                            del self.room_counters[room_id]

            if client in self.usernames:
                del self.usernames[client]

            client.close()
            print(f"[SERVER] Отключение от {address}")

    def get_board_state(self, board):
        """Получить состояние доски в удобном формате"""
        return {
            'fen': board.fen(),
            'turn': 'white' if board.turn == chess.WHITE else 'black',
            'legal_moves': [str(move) for move in board.legal_moves],
            'is_check': board.is_check(),
            'is_checkmate': board.is_checkmate(),
            'is_stalemate': board.is_stalemate(),
            'fullmove_number': board.fullmove_number
        }

    def start(self):
        """Запуск сервера"""
        self.server.listen()
        print("[SERVER] Ожидание подключений...")

        try:
            while True:
                client, address = self.server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client, address))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\n[SERVER] Остановка сервера...")
            self.server.close()
            sys.exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Шахматный сервер')
    parser.add_argument('--host', default='0.0.0.0', help='Хост сервера')
    parser.add_argument('--port', type=int, default=5555, help='Порт сервера')

    args = parser.parse_args()

    server = ChessServer(host=args.host, port=args.port)
    server.start()