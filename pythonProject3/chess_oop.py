import chess
import chess.pgn
from datetime import datetime


class Chess_OOP():
    def __init__(self):
        self.board = chess.Board()
        self.player_num = int()
        self.player_color = str()
        self.move_input = str()
        self.loaded_game = None
        self.current_node = None
        self.is_review_mode = False
        self.game_history = []
        self.game_history_san = []

    def print_board(self):
        b0ard = self.board
        board_str = str(b0ard).split('\n')

        print("\n    A    B    C    D    E    F    G    H\n")

        for i, line in enumerate(board_str):
            row_num = 8 - i
            chars = line.split()
            formatted_line = "  "
            for j, char in enumerate(chars):
                if j == 0:
                    formatted_line += char + "  "
                else:
                    formatted_line += "  " + char + "  "

            print(f"{row_num} {formatted_line} {row_num}")
        print("\n    A    B    C    D    E    F    G    H\n")

    def Rule(self):
        print("Правила перед игрой:\n"
              "     Пример хода для пешек: e2e4 или e4; \n"
              "     Для остальных фигур: например конь - Nf6 \n"
              "     взятие одной фигуры другой: e4xd5 - для пешки, например \n"
              "     поставить шах: Qd8+, поставить мат: Qd8# \n"
              "     рокировка: короткая через O-O, длинная через O-O-O, можно также e8c8 \n"
              "     превращение пешки в конце: e8=Q или e7e8q \n"
              "     1 игрок-белые, имеет заглавные буквы на поле; "
              "2 игрок-черные, имеет обычные буквы на поле \n"
              "     Использовать фигуры шахматной доски оба игрока должны заглавными буквами: \n"
              "     Q, K, N, R, B, для пешки не нужны буквы")

    def show_legal_moves(self):
        moves = list(self.board.legal_moves)
        print(f"Доступные ходы ({len(moves)}):")
        san_moves = [self.board.san(move) if hasattr(self.board, 'san') else str(move) for move in moves]
        for i in range(0, len(san_moves), 8):
            row = san_moves[i:i + 8]
            print("  " + "  ".join(row))
        print()

    def show_available_moves(self, square_str):
        try:
            from_square = chess.parse_square(square_str.lower())
            piece = self.board.piece_at(from_square)
            if not piece:
                print(f"На поле {square_str.upper()} нет фигуры!")
                return

            moves = [move for move in self.board.legal_moves if move.from_square == from_square]
            if not moves:
                print(f"У фигуры на {square_str.upper()} нет доступных ходов!")
                return

            piece_names = {
                'P': 'пешка', 'N': 'конь', 'B': 'слон',
                'R': 'ладья', 'Q': 'ферзь', 'K': 'король',
                'p': 'пешка', 'n': 'конь', 'b': 'слон',
                'r': 'ладья', 'q': 'ферзь', 'k': 'король'
            }

            piece_name = piece_names.get(piece.symbol(), 'фигура')
            print(f"Доступные ходы для {piece_name} на {square_str.upper()}:")

            empty_moves = [move for move in moves if not self.board.piece_at(move.to_square)]
            capture_moves = [move for move in moves if self.board.piece_at(move.to_square)]

            if empty_moves:
                print("На пустые клетки:")
                empty_sans = [self.board.san(move) for move in empty_moves]
                for i in range(0, len(empty_sans), 8):
                    print("    " + " ".join(empty_sans[i:i + 8]))

            if capture_moves:
                print("Для взятия фигур:")
                capture_sans = [self.board.san(move) for move in capture_moves]
                for i in range(0, len(capture_sans), 8):
                    print("    " + " ".join(capture_sans[i:i + 8]))

        except ValueError:
            print(f"Неверное обозначение поля: {square_str}")

    def show_threatened_pieces(self):
        current_player = self.board.turn
        player_color = "белых" if current_player else "черных"
        threatened_pieces = []

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece and piece.color == current_player:
                attackers = self.board.attackers(not current_player, square)
                if attackers:
                    piece_names = {
                        'P': 'пешка', 'N': 'конь', 'B': 'слон',
                        'R': 'ладья', 'Q': 'ферзь', 'K': 'король'
                    }
                    piece_name = piece_names.get(piece.symbol().upper(), 'фигура')
                    square_name = chess.square_name(square).upper()
                    attackers_list = [piece_names.get(self.board.piece_at(s).symbol().upper(), 'фигура')
                                      for s in attackers if self.board.piece_at(s)]

                    threatened_pieces.append({
                        'piece': piece_name,
                        'square': square_name,
                        'attackers': attackers_list
                    })

        print(f"Фигуры {player_color.upper()} под угрозой: ")
        if not threatened_pieces:
            print(f"У {player_color} нет фигур под угрозой")
        else:
            for item in threatened_pieces:
                attackers_str = ", ".join(item['attackers'])
                print(f"  - {item['piece']} на {item['square']} (угрожают: {attackers_str})")

        if self.board.is_check():
            king_color = "белого" if current_player else "черного"
            print(f"Внимание шах {king_color.upper()}")

    def back_move(self, num_move=1):
        if len(self.board.move_stack) < num_move:
            print("Нельзя откатить ходы")
            return False

        for i in range(num_move):
            move = self.board.pop()
            if self.game_history:
                self.game_history.pop()
            if self.game_history_san:
                self.game_history_san.pop()
            print(f"Отменили ход {move}, {i + 1} по счету")

        self.print_board()
        return True

    def help_command(self):
        try:
            if self.is_review_mode:
                player_color = "белых" if self.board.turn else "черных"
                self.move_input = input(f"Просмотр партии ({player_color} ходят) [help для помощи]: ").strip()
            else:
                player_color = "белых" if self.board.turn else "черных"
                self.move_input = input(f"Игрок {self.player_num} ({player_color}): ").strip()

            if self.move_input.lower() in ['?', 'help', 'помощь']:
                print("Все команды 'помогаторы': \n"
                      "? - показать эту справку \n"
                      "moves [поле] - показать ходы фигуры (пример: moves e2) \n"
                      "threats - показать фигуры под угрозой \n"
                      "legal - показать все возможные ходы \n"
                      "back - отменить последний ход \n"
                      "back [число] - отменить несколько ходов (пример: back 3) \n"
                      "load - загрузить партию из файла PGN \n"
                      "save - сохранить текущую партию в PGN \n"
                      "review - перейти в режим просмотра (если партия загружена) \n"
                      "play - перейти в режим игры \n"
                      "prev - предыдущий ход (в режиме просмотра) \n"
                      "next - следующий ход (в режиме просмотра) \n"
                      "first - к началу партии (в режиме просмотра) \n"
                      "last - к концу партии (в режиме просмотра) \n"
                      "exit - выйти из игры")
                return self.help_command()

            elif self.move_input.startswith('moves '):
                square = self.move_input[6:].strip()
                if square:
                    self.show_available_moves(square)
                else:
                    print("Используйте moves X (где X - поле фигуры)")
                return self.help_command()

            elif self.move_input == 'threats':
                self.show_threatened_pieces()
                return self.help_command()

            elif self.move_input == 'legal':
                self.show_legal_moves()
                return self.help_command()

            elif self.move_input == 'back':
                if self.back_move(1):
                    if self.is_review_mode and self.current_node and self.current_node.parent:
                        self.current_node = self.current_node.parent
                return self.get_move_input()

            elif self.move_input.startswith('back '):
                try:
                    num = int(self.move_input.split()[1])
                    if self.back_move(num):
                        if self.is_review_mode:
                            for _ in range(num):
                                if self.current_node and self.current_node.parent:
                                    self.current_node = self.current_node.parent
                    return self.get_move_input()
                except:
                    print("Используйте back или back X, где X - число ходов)")
                return self.help_command()

            elif self.move_input == 'load':
                self.load_game()
                return self.help_command()

            elif self.move_input == 'save':
                self.save_game()
                return self.help_command()

            elif self.move_input == 'review':
                if self.loaded_game:
                    self.enter_review_mode()
                else:
                    print("Сначала загрузите партию командой 'load'")
                return self.help_command()

            elif self.move_input == 'play':
                self.exit_review_mode()
                return self.help_command()

            elif self.move_input == 'prev' and self.is_review_mode:
                self.review_previous_move()
                return self.help_command()

            elif self.move_input == 'next' and self.is_review_mode:
                self.review_next_move()
                return self.help_command()

            elif self.move_input == 'first' and self.is_review_mode:
                self.review_first_move()
                return self.help_command()

            elif self.move_input == 'last' and self.is_review_mode:
                self.review_last_move()
                return self.help_command()

            elif self.move_input == 'exit':
                print("Игра завершена.")
                exit()

            return None

        except KeyboardInterrupt:
            print("Игра прервана.")
            exit()
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    def get_move_input(self):
        self.player_num = 1 if self.board.turn else 2

        while True:
            try:
                self.help_command()
                move = None
                processed_input = self.move_input

                if "=" in processed_input:
                    processed_input = processed_input.replace("=", "").lower()
                elif processed_input and processed_input[-1].lower() in ['q', 'r', 'b', 'n']:
                    processed_input = processed_input.lower()

                # Пробуем UCI
                try:
                    move = chess.Move.from_uci(processed_input)
                    if move in self.board.legal_moves:
                        if not self.is_review_mode:
                            self.game_history.append(move)
                            try:
                                temp_board = chess.Board()
                                self.game_history_san = []
                                for m in self.game_history:
                                    san_move = temp_board.san(m)
                                    self.game_history_san.append(san_move)
                                    temp_board.push(m)
                            except:
                                self.game_history_san = [str(m) for m in self.game_history]
                        return move
                except:
                    pass

                # Пробуем SAN
                try:
                    move = self.board.parse_san(self.move_input)
                    if move in self.board.legal_moves:
                        if not self.is_review_mode:
                            self.game_history.append(move)
                            try:
                                temp_board = chess.Board()
                                self.game_history_san = []
                                for m in self.game_history:
                                    san_move = temp_board.san(m)
                                    self.game_history_san.append(san_move)
                                    temp_board.push(m)
                            except:
                                self.game_history_san = [str(m) for m in self.game_history]
                        return move
                except:
                    pass

                print("Неверный ход. Введите ? для помощи")
                self.show_legal_moves()

            except KeyboardInterrupt:
                print("Игра прервана.")
                exit()
            except Exception as e:
                print(f"Ошибка: {e}")

    def handle_game_over(self):
        if self.board.is_checkmate():
            winner = "белые" if not self.board.turn else "черные"
            print(f"Мат, победили {winner}!")
            return True
        elif self.board.is_stalemate() or self.board.is_insufficient_material():
            print("Пат или ничья")
            return True
        elif self.board.is_seventyfive_moves():
            print("Правило 75 ходов - ничья")
            return True
        elif self.board.is_fivefold_repetition():
            print("Пятикратное повторение позиции - ничья")
            return True
        elif self.board.is_check():
            print("Шах")
        return False

    def load_game(self):
        try:
            filename = input("Введите имя файла PGN: ").strip()

            if not filename.endswith('.pgn'):
                filename += '.pgn'

            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.loaded_game = chess.pgn.read_game(f)
            except FileNotFoundError:
                print(f"Файл {filename} не найден!")
                return

            if self.loaded_game:
                self.current_node = self.loaded_game
                moves = list(self.loaded_game.mainline_moves())

                if moves:
                    self.board = self.loaded_game.board()
                    self.game_history = []
                    self.game_history_san = []

                    temp_board = chess.Board()
                    for move in moves:
                        self.game_history.append(move)
                        try:
                            san_move = temp_board.san(move)
                            self.game_history_san.append(san_move)
                        except:
                            self.game_history_san.append(str(move))
                        temp_board.push(move)

                    self.board = self.loaded_game.board()
                    self.current_node = self.loaded_game

                    print(f"\n✓ Партия загружена успешно!")

                    white = self.loaded_game.headers.get('White', 'Неизвестно')
                    black = self.loaded_game.headers.get('Black', 'Неизвестно')
                    result = self.loaded_game.headers.get('Result', '*')

                    print(f"Белые: {white}")
                    print(f"Черные: {black}")
                    print(f"Результат: {result}")
                    print(f"Количество ходов: {len(moves)}")

                    if moves:
                        print("\nПервые ходы:")
                        temp_board = chess.Board()
                        move_count = 0
                        for i, move in enumerate(moves[:10]):
                            san_move = temp_board.san(move)
                            if i % 2 == 0:
                                move_count += 1
                                print(f"{move_count}. {san_move}", end=" ")
                            else:
                                print(f"{san_move}")
                            temp_board.push(move)
                        if len(moves[:10]) % 2 == 1:
                            print()
                else:
                    print("Партия пустая (нет ходов)")
            else:
                print("Не удалось загрузить партию из файла")

        except Exception as e:
            print(f"Ошибка при загрузке партии: {e}")

    def save_game(self):
        try:
            if not self.game_history:
                print("Нет истории ходов для сохранения!")
                return

            game = chess.pgn.Game()

            game.headers["Event"] = "Шахматная партия"
            game.headers["Site"] = "Python Chess"
            game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
            game.headers["Round"] = "1"
            game.headers["White"] = "Игрок 1"
            game.headers["Black"] = "Игрок 2"
            game.headers["Result"] = "*"

            node = game
            temp_board = chess.Board()

            for move in self.game_history:
                node = node.add_variation(move)
                temp_board.push(move)

            if temp_board.is_checkmate():
                game.headers["Result"] = "1-0" if temp_board.turn == chess.BLACK else "0-1"
            elif temp_board.is_stalemate() or temp_board.is_insufficient_material():
                game.headers["Result"] = "1/2-1/2"

            filename = input("Введите имя файла для сохранения: ").strip()
            if not filename:
                filename = "game"
            if not filename.endswith('.pgn'):
                filename += ".pgn"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(str(game))

            print(f"\n✓ Партия сохранена в файл: {filename}")
            print(f"Количество ходов: {len(self.game_history)}")

        except Exception as e:
            print(f"Ошибка при сохранении партии: {e}")

    def enter_review_mode(self):
        if not self.loaded_game:
            print("Нет загруженной партии!")
            return

        self.is_review_mode = True
        self.current_node = self.loaded_game
        self.board = self.loaded_game.board()

        print("\n" + "=" * 50)
        print("РЕЖИМ ПРОСМОТРА ПАРТИИ")
        print("=" * 50)
        print("Команды: prev, next, first, last, play")

        white = self.loaded_game.headers.get('White', 'Неизвестно')
        black = self.loaded_game.headers.get('Black', 'Неизвестно')
        print(f"Белые: {white}")
        print(f"Черные: {black}")
        print("=" * 50)

        self.print_board()
        print(f"Позиция: начало партии")
        print(f"Всего ходов: {len(self.game_history)}")

    def exit_review_mode(self):
        self.is_review_mode = False
        print("\nРежим просмотра завершен. Возвращаемся к игре.")

        if self.game_history:
            self.board = chess.Board()
            for move in self.game_history:
                self.board.push(move)
        else:
            self.board = chess.Board()

    def get_current_move_number(self):
        if not self.current_node:
            return 0

        move_count = 0
        node = self.loaded_game
        while node != self.current_node and node.variations:
            node = node.variations[0]
            move_count += 1

        return (move_count // 2) + 1 if move_count > 0 else 0

    def review_previous_move(self):
        if not self.current_node or not self.current_node.parent:
            print("Уже в начале партии")
            return

        self.current_node = self.current_node.parent
        self.board = self.current_node.board()

        self.print_board()
        move_number = self.get_current_move_number()

        if move_number > 0:
            print(f"Перешли к позиции после хода {move_number}")
            if self.current_node.move and self.current_node.parent:
                try:
                    san_move = self.current_node.parent.board().san(self.current_node.move)
                    print(f"Последний ход: {san_move}")
                except:
                    print(f"Последний ход: {self.current_node.move}")
        else:
            print("Начальная позиция")

    def review_next_move(self):
        if not self.current_node or not self.current_node.variations:
            print("Уже в конце партии")
            return

        self.current_node = self.current_node.variations[0]
        self.board = self.current_node.board()

        self.print_board()
        move_number = self.get_current_move_number()
        print(f"Перешли к ходу {move_number}")

        if self.current_node.move and self.current_node.parent:
            try:
                san_move = self.current_node.parent.board().san(self.current_node.move)
                print(f"Ход: {san_move}")
            except:
                print(f"Ход: {self.current_node.move}")

    def review_first_move(self):
        if not self.loaded_game:
            return

        self.current_node = self.loaded_game
        self.board = self.loaded_game.board()

        self.print_board()
        print("Начальная позиция")

    def review_last_move(self):
        if not self.loaded_game:
            return

        self.current_node = self.loaded_game
        while self.current_node.variations:
            self.current_node = self.current_node.variations[0]

        self.board = self.current_node.board()

        self.print_board()
        move_number = self.get_current_move_number()
        print(f"Конец партии (ход {move_number})")

        if self.board.is_checkmate():
            print("МАТ!")
        elif self.board.is_stalemate():
            print("ПАТ!")

    def game(self):
        self.Rule()
        move_count = 1

        while not self.board.is_game_over():
            self.print_board()
            move = self.get_move_input()
            self.board.push(move)

            try:
                san_move = self.board.san(move)
                print(f"Ход {move_count}: {san_move}")
            except:
                print(f"Ход {move_count}: {move}")

            move_count += 1

            if self.handle_game_over():
                break

        self.print_board()
        print(f"Игра окончена. Результат: {self.board.result()}")

        while True:
            again = input("Сыграть еще? (да/нет): ").lower().strip()
            if again in ['да', 'yes', 'y', 'д']:
                self.__init__()
                self.game()
                break
            elif again in ['нет', 'no', 'n', 'н']:
                print("Спасибо за игру!")
                break
            else:
                print("Введите 'да' или 'нет'")


if __name__ == "__main__":
    chess_main = Chess_OOP()
    chess_main.game()