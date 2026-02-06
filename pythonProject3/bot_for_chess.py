import chess
import random
import time


class MinMaxBot:
    """Бот с алгоритмом минимакс (максимальная сложность)"""

    def __init__(self):
        self.name = "Бот (макс. сложность)"
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

    def evaluate_position(self, board: chess.Board) -> float:
        """Оценка позиции с продвинутыми эвристиками"""
        if board.is_checkmate():
            return -100000 if board.turn else 100000

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0

        # Материальный счет
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value

                # Бонус за центральные поля для пешек и фигур
                file, rank = chess.square_file(square), chess.square_rank(square)
                center_bonus = 0
                if 2 <= file <= 5 and 2 <= rank <= 5:
                    center_bonus = 10 * value / 100
                elif 3 <= file <= 4 and 3 <= rank <= 4:
                    center_bonus = 20 * value / 100

                if piece.color == chess.WHITE:
                    score += center_bonus
                else:
                    score -= center_bonus

        # Мобильность (количество возможных ходов)
        score += len(list(board.legal_moves)) * 5 * (1 if board.turn else -1)

        # Безопасность короля
        king_square = board.king(board.turn)
        if king_square:
            file, rank = chess.square_file(king_square), chess.square_rank(king_square)
            if rank == (0 if board.turn else 7):  # Король в углу
                score += -30 * (1 if board.turn else -1)
            elif file in [0, 7] or rank in [0, 7]:  # Король на краю
                score += -20 * (1 if board.turn else -1)

        # Шах
        if board.is_check():
            score += -50 * (1 if board.turn else -1)

        return score

    def minimax(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """Алгоритм минимакс с альфа-бета отсечением (рекурсивный)"""
        if depth == 0 or board.is_game_over():
            return self.evaluate_position(board)

        legal_moves = list(board.legal_moves)

        if maximizing:
            max_eval = -float('inf')
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_move(self, board: chess.Board) -> chess.Move:
        """Получить лучший ход"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise Exception("Нет возможных ходов")

        best_move = None
        best_value = -float('inf')

        # Увеличиваем глубину поиска для большей сложности
        depth = 3  # Можно увеличить для еще большей сложности

        for move in legal_moves:
            board.push(move)
            move_value = self.minimax(board, depth - 1, -float('inf'), float('inf'), False)
            board.pop()

            if move_value > best_value:
                best_value = move_value
                best_move = move
            elif move_value == best_value and random.random() > 0.5:
                # Если оценки равны, выбираем случайно для разнообразия
                best_move = move

        return best_move


class Chess_OOP():
    def __init__(self):
        self.board = chess.Board()
        self.bot_white = MinMaxBot()
        self.bot_black = MinMaxBot()

    def print_board(self):
        b0ard = self.board
        board_str = str(b0ard).split('\n')

        print("  a  b  c  d  e  f  g  h \n")
        for i, line in enumerate(board_str):
            row_num = 8 - i
            chars = line.split()
            formatted_line = ""
            for j, char in enumerate(chars):
                if j == 0:
                    formatted_line += char
                elif j == 1:
                    formatted_line += "  " + char
                elif j == 2:
                    formatted_line += "  " + char
                elif j == 3:
                    formatted_line += "  " + char
                elif j == 4:
                    formatted_line += "  " + char
                elif j == 5:
                    formatted_line += "  " + char
                elif j == 6:
                    formatted_line += "  " + char
                elif j == 7:
                    formatted_line += "  " + char

            print(f"{row_num} {formatted_line} {row_num}")
        print("\n  A  B  C  D  E  F  G  H\n")

        # Показываем чей ход
        if self.board.turn:
            print("Ход белых (бот)")
        else:
            print("Ход черных (бот)")

        # Показываем статус игры
        if self.board.is_checkmate():
            print("\n шах и мат")
        elif self.board.is_stalemate():
            print("\n пат или ничья")
        elif self.board.is_insufficient_material():
            print("\n ничья ")
        elif self.board.is_check():
            print("\n шах ")

    def handle_game_over(self):
        if self.board.is_checkmate():
            winner = "белые" if not self.board.turn else "черные"
            print('-' * 50)
            print(f"Мат. Победили {winner.upper()}!")
            print('-' * 50)
            return True
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or \
                self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition():
            print('-' * 50)
            print("Пат/Ничья")
            print('-' * 50)
            return True
        return False

    def game(self):
        print("-" * 40)
        print("БОТ ПРОТИВ БОТА - МАКСИМАЛЬНАЯ СЛОЖНОСТЬ".center(60))
        print("-" * 40)
        print("\nНастройки:")
        print(f"- Два одинаковых бота максимальной сложности")
        print("- Белые: Бот 1")
        print("- Черные: Бот 2")
        print("\n" + "-" * 40)

        move_count = 1
        input("\nНажмите Enter для начала игры...")

        while not self.board.is_game_over():
            self.print_board()
            current_bot = self.bot_white if self.board.turn else self.bot_black
            bot_name = "Бот 1 (белые)" if self.board.turn else "Бот 2 (черные)"
            try:
                move = current_bot.get_move(self.board)
                self.board.push(move)
                try:
                    san_move = self.board.san(move)
                    print(f"\nХод {move_count}: {bot_name} → {san_move}")
                except:
                    print(f"\nХод {move_count}: {bot_name} → {move}")

                move_count += 1

                if self.handle_game_over():
                    break

            except Exception as e:
                print(f"\nОшибка при ходе бота: {e}")
                break
        self.print_board()
        print(f"\nИгра завершена. Всего ходов: {move_count - 1}")
        print("\n" + "-" * 40 + "\n"
        "Статистика в игре: \n"
        f"Всего ходов: {move_count - 1}")

        white_pieces = sum(1 for square in chess.SQUARES if
                           self.board.piece_at(square) and self.board.piece_at(square).color == chess.WHITE)
        black_pieces = sum(1 for square in chess.SQUARES if
                           self.board.piece_at(square) and self.board.piece_at(square).color == chess.BLACK)
        print(f"Фигур осталось у белых: {white_pieces}")
        print(f"Фигур осталось у черных: {black_pieces} \n")
        print("-" * 40)

        while True:
            again = input("\nХотите посмотреть еще одну партию? (да/нет): ").lower()
            match again:
                case 'да':
                    self.__init__()
                    self.game()
                    break
                case 'нет':
                    print("\n Конец игры.")
                    break
                case _:
                    print("Пожалуйста, введите 'да' или 'нет'.")


if __name__ == "__main__":
    game = Chess_OOP()
    game.game()