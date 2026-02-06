import pickle


class Color:
    """Класс для представления цвета фигур"""
    white_figure = "WHITE"
    black_figure = "BLACK"

    def __init__(self, value):
        if value not in [self.white_figure, self.black_figure]:
            raise ValueError(f"Некорректное значение цвета: {value}")
        self.value = value

    @classmethod
    def white(cls):
        """Создание белого цвета"""
        return cls(cls.white_figure)

    @classmethod
    def black(cls):
        """Создание черного цвета"""
        return cls(cls.black_figure)

    def opposite(self):
        """Получить противоположный цвет"""
        if self.value == self.white_figure:
            return Color(self.black_figure)
        else:
            return Color(self.white_figure)

    def __str__(self):
        return "белые" if self.value == self.white_figure else "черные"

    def __eq__(self, other):
        if not isinstance(other, Color):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)


class Square:
    """Класс для представления клетки на шахматной доске"""
    FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    RANKS = ['1', '2', '3', '4', '5', '6', '7', '8']

    def __init__(self, file, rank):
        if not (0 <= file <= 7 and 0 <= rank <= 7):
            raise ValueError(f"Некорректные координаты: file={file}, rank={rank}")
        self.file = file  # 0-7 (a-h)
        self.rank = rank  # 0-7 (1-8)

    @classmethod
    def from_string(cls, notation):
        """Создание квадрата из строковой нотации (например, 'e4')"""
        if len(notation) != 2:
            raise ValueError(f"Некорректная нотация: {notation}")

        file_char = notation[0].lower()
        rank_char = notation[1]

        try:
            file_idx = cls.FILES.index(file_char)
            rank_idx = int(rank_char) - 1
        except (ValueError, IndexError):
            raise ValueError(f"Некорректная нотация: {notation}")

        return cls(file_idx, rank_idx)

    @classmethod
    def from_index(cls, index):
        """Создание квадрата из индекса 0-63"""
        if not (0 <= index <= 63):
            raise ValueError(f"Некорректный индекс: {index}")
        file = index % 8
        rank = index // 8
        return cls(file, rank)

    def to_index(self):
        """Преобразование в индекс 0-63"""
        return self.rank * 8 + self.file

    def to_string(self):
        """Преобразование в строковую нотацию (например, 'e4')"""
        return f"{self.FILES[self.file]}{self.RANKS[self.rank]}"

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        if not isinstance(other, Square):
            return False
        return self.file == other.file and self.rank == other.rank

    def __hash__(self):
        return hash((self.file, self.rank))

    def is_valid(self):
        """Проверка, находится ли квадрат на доске"""
        return 0 <= self.file <= 7 and 0 <= self.rank <= 7

    def offset(self, file_delta, rank_delta):
        """Создание нового квадрата со смещением, возвращает None если за пределами доски"""
        new_file = self.file + file_delta
        new_rank = self.rank + rank_delta

        if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
            return Square(new_file, new_rank)
        return None


class Move:
    """Класс для представления хода"""

    def __init__(self, from_square, to_square, promotion=None):
        self.from_square = from_square
        self.to_square = to_square
        self.promotion = promotion  # 'Q', 'R', 'B', 'N' или None

    def __str__(self):
        result = f"{self.from_square}{self.to_square}"
        if self.promotion:
            result += f"={self.promotion}"
        return result

    def __eq__(self, other):
        if not isinstance(other, Move):
            return False
        return (self.from_square == other.from_square and
                self.to_square == other.to_square and
                self.promotion == other.promotion)

    def __hash__(self):
        return hash((self.from_square, self.to_square, self.promotion))

    @classmethod
    def from_string(cls, notation):
        """Создание хода из строковой нотации (UCI или SAN)"""
        # Пока реализуем только UCI
        if len(notation) >= 4:
            from_sq = Square.from_string(notation[:2])
            to_sq = Square.from_string(notation[2:4])
            promotion = notation[4] if len(notation) > 4 else None
            return cls(from_sq, to_sq, promotion)
        raise ValueError(f"Некорректная нотация хода: {notation}")


class Piece:
    """Базовый класс для шахматных фигур"""

    def __init__(self, color, symbol, name):
        if not isinstance(color, Color):
            raise ValueError("color должен быть экземпляром Color")
        self.color = color
        self.symbol = symbol
        self.name = name
        self.has_moved = False

    def get_moves(self, board, square):
        """Получение всех возможных ходов для фигуры - должен быть переопределен в подклассах"""
        raise NotImplementedError("Метод get_moves должен быть реализован в подклассе")

    def get_attacked_squares(self, board, square):
        """Получение всех атакуемых клеток (даже занятых своими фигурами)"""
        attacked = set()

        if self.name == "пешка":
            direction = 1 if self.color.value == Color.white_figure else -1
            for file_delta in [-1, 1]:
                target = square.offset(file_delta, direction)
                if target is not None:
                    attacked.add(target)

        elif self.name == "конь":
            knight_moves = [
                (2, 1), (2, -1), (-2, 1), (-2, -1),
                (1, 2), (1, -2), (-1, 2), (-1, -2)
            ]
            for dx, dy in knight_moves:
                target = square.offset(dx, dy)
                if target is not None:
                    attacked.add(target)

        elif self.name == "слон":
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dx, dy in directions:
                for i in range(1, 8):
                    target = square.offset(dx * i, dy * i)
                    if target is not None:
                        attacked.add(target)
                        piece_at_target = board.get_piece_at(target)
                        if piece_at_target:
                            break
                    else:
                        break

        elif self.name == "ладья":
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for dx, dy in directions:
                for i in range(1, 8):
                    target = square.offset(dx * i, dy * i)
                    if target is not None:
                        attacked.add(target)
                        piece_at_target = board.get_piece_at(target)
                        if piece_at_target:
                            break
                    else:
                        break

        elif self.name == "ферзь":
            directions = [
                (1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ]
            for dx, dy in directions:
                for i in range(1, 8):
                    target = square.offset(dx * i, dy * i)
                    if target is not None:
                        attacked.add(target)
                        piece_at_target = board.get_piece_at(target)
                        if piece_at_target:
                            break
                    else:
                        break

        elif self.name == "король":
            king_moves = [
                (1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ]
            for dx, dy in king_moves:
                target = square.offset(dx, dy)
                if target is not None:
                    attacked.add(target)

        return attacked

    def __str__(self):
        return self.symbol if self.color.value == Color.white_figure else self.symbol.lower()

    def get_display_name(self):
        """Получение отображаемого имени на русском"""
        color_str = "белая" if self.color.value == Color.white_figure else "черная"
        return f"{color_str} {self.name}"


class Pawn(Piece):
    """Класс для пешки"""

    def __init__(self, color):
        super().__init__(color, 'P', 'пешка')
        self.direction = 1 if color.value == Color.white_figure else -1

    def get_moves(self, board, square):
        moves = []

        # Ход вперед на одну клетку
        forward_one = square.offset(0, self.direction)
        if forward_one is not None and board.get_piece_at(forward_one) is None:
            moves.append(Move(square, forward_one))

            # Ход вперед на две клетки (только с начальной позиции)
            if ((self.color.value == Color.white_figure and square.rank == 1) or
                    (self.color.value == Color.black_figure and square.rank == 6)):
                forward_two = square.offset(0, 2 * self.direction)
                if forward_two is not None and board.get_piece_at(forward_two) is None:
                    moves.append(Move(square, forward_two))

        # Взятия
        for file_delta in [-1, 1]:
            capture_square = square.offset(file_delta, self.direction)
            if capture_square is not None:
                target_piece = board.get_piece_at(capture_square)
                if target_piece is not None and target_piece.color.value != self.color.value:
                    moves.append(Move(square, capture_square))

        # Превращения
        promotion_rank = 7 if self.color.value == Color.white_figure else 0
        if square.rank == promotion_rank - self.direction:
            promotion_moves = []
            for move in moves:
                if move.to_square.rank == promotion_rank:
                    for promo_piece in ['Q', 'R', 'B', 'N']:
                        promotion_moves.append(
                            Move(move.from_square, move.to_square, promo_piece)
                        )
            return promotion_moves

        return moves


class Knight(Piece):
    """Класс для коня"""

    def __init__(self, color):
        super().__init__(color, 'N', 'конь')

    def get_moves(self, board, square):
        moves = []
        knight_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]

        for dx, dy in knight_moves:
            target_square = square.offset(dx, dy)
            if target_square is not None:
                target_piece = board.get_piece_at(target_square)
                if target_piece is None or target_piece.color.value != self.color.value:
                    moves.append(Move(square, target_square))

        return moves


class Bishop(Piece):
    """Класс для слона"""

    def __init__(self, color):
        super().__init__(color, 'B', 'слон')

    def get_moves(self, board, square):
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

        for dx, dy in directions:
            for i in range(1, 8):
                target_square = square.offset(dx * i, dy * i)
                if target_square is not None:
                    target_piece = board.get_piece_at(target_square)
                    if target_piece is None:
                        moves.append(Move(square, target_square))
                    elif target_piece.color.value != self.color.value:
                        moves.append(Move(square, target_square))
                        break
                    else:
                        break
                else:
                    break

        return moves


class Rook(Piece):
    """Класс для ладьи"""

    def __init__(self, color):
        super().__init__(color, 'R', 'ладья')

    def get_moves(self, board, square):
        moves = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for dx, dy in directions:
            for i in range(1, 8):
                target_square = square.offset(dx * i, dy * i)
                if target_square is not None:
                    target_piece = board.get_piece_at(target_square)
                    if target_piece is None:
                        moves.append(Move(square, target_square))
                    elif target_piece.color.value != self.color.value:
                        moves.append(Move(square, target_square))
                        break
                    else:
                        break
                else:
                    break

        return moves


class Queen(Piece):
    """Класс для ферзя"""

    def __init__(self, color):
        super().__init__(color, 'Q', 'ферзь')

    def get_moves(self, board, square):
        moves = []
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]

        for dx, dy in directions:
            for i in range(1, 8):
                target_square = square.offset(dx * i, dy * i)
                if target_square is not None:
                    target_piece = board.get_piece_at(target_square)
                    if target_piece is None:
                        moves.append(Move(square, target_square))
                    elif target_piece.color.value != self.color.value:
                        moves.append(Move(square, target_square))
                        break
                    else:
                        break
                else:
                    break

        return moves


class King(Piece):
    """Класс для короля"""

    def __init__(self, color):
        super().__init__(color, 'K', 'король')

    def get_moves(self, board, square):
        moves = []
        king_moves = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]

        for dx, dy in king_moves:
            target_square = square.offset(dx, dy)
            if target_square is not None:
                target_piece = board.get_piece_at(target_square)
                if target_piece is None or target_piece.color.value != self.color.value:
                    moves.append(Move(square, target_square))

        # Рокировка
        if not self.has_moved:
            # Короткая рокировка
            rook_square = Square(7, square.rank)
            rook = board.get_piece_at(rook_square)
            if (rook is not None and isinstance(rook, Rook) and not rook.has_moved and
                    board.get_piece_at(Square(5, square.rank)) is None and
                    board.get_piece_at(Square(6, square.rank)) is None):
                moves.append(Move(square, Square(6, square.rank)))

            # Длинная рокировка
            rook_square = Square(0, square.rank)
            rook = board.get_piece_at(rook_square)
            if (rook is not None and isinstance(rook, Rook) and not rook.has_moved and
                    board.get_piece_at(Square(1, square.rank)) is None and
                    board.get_piece_at(Square(2, square.rank)) is None and
                    board.get_piece_at(Square(3, square.rank)) is None):
                moves.append(Move(square, Square(2, square.rank)))

        return moves


class Board:
    """Класс для шахматной доски"""

    def __init__(self):
        self.squares = {}
        self.current_turn = Color.white()
        self.move_history = []
        self.castling_rights = {
            Color.white(): {'king_side': True, 'queen_side': True},
            Color.black(): {'king_side': True, 'queen_side': True}
        }
        self.en_passant_target = None

        # Инициализация пустой доски
        for file in range(8):
            for rank in range(8):
                self.squares[Square(file, rank)] = None

        # Расстановка фигур
        self._setup_pieces()

    def _setup_pieces(self):
        """Расстановка фигур в начальной позиции"""
        # Белые фигуры
        white_color = Color.white()
        black_color = Color.black()

        # Пешки белые
        for file in range(8):
            self.squares[Square(file, 1)] = Pawn(white_color)

        # Остальные фигуры белые
        self.squares[Square(0, 0)] = Rook(white_color)
        self.squares[Square(1, 0)] = Knight(white_color)
        self.squares[Square(2, 0)] = Bishop(white_color)
        self.squares[Square(3, 0)] = Queen(white_color)
        self.squares[Square(4, 0)] = King(white_color)
        self.squares[Square(5, 0)] = Bishop(white_color)
        self.squares[Square(6, 0)] = Knight(white_color)
        self.squares[Square(7, 0)] = Rook(white_color)

        # Пешки черные
        for file in range(8):
            self.squares[Square(file, 6)] = Pawn(black_color)

        # Остальные фигуры черные
        self.squares[Square(0, 7)] = Rook(black_color)
        self.squares[Square(1, 7)] = Knight(black_color)
        self.squares[Square(2, 7)] = Bishop(black_color)
        self.squares[Square(3, 7)] = Queen(black_color)
        self.squares[Square(4, 7)] = King(black_color)
        self.squares[Square(5, 7)] = Bishop(black_color)
        self.squares[Square(6, 7)] = Knight(black_color)
        self.squares[Square(7, 7)] = Rook(black_color)

    def get_piece_at(self, square):
        """Получение фигуры на указанной клетке"""
        return self.squares.get(square)

    def is_square_attacked(self, square, by_color):
        """Проверка, атакована ли клетка фигурами указанного цвета"""
        for from_square, piece in self.squares.items():
            if piece is not None and piece.color.value == by_color.value:
                attacked_squares = piece.get_attacked_squares(self, from_square)
                if square in attacked_squares:
                    return True
        return False

    def is_in_check(self, color):
        """Проверка, находится ли король указанного цвета под шахом"""
        # Находим короля
        king_square = None
        for square, piece in self.squares.items():
            if isinstance(piece, King) and piece.color.value == color.value:
                king_square = square
                break

        if king_square is None:
            return False

        return self.is_square_attacked(king_square, color.opposite())

    def get_legal_moves(self, color):
        """Получение всех легальных ходов для указанного цвета"""
        legal_moves = []

        for from_square, piece in self.squares.items():
            if piece is not None and piece.color.value == color.value:
                # Получаем все возможные ходы для фигуры
                piece_moves = piece.get_moves(self, from_square)

                # Фильтруем ходы, которые оставляют своего короля под шахом
                for move in piece_moves:
                    # Создаем копию доски и делаем ход
                    test_board = self.copy()

                    # Упрощенный make_move для тестирования
                    test_piece = test_board.get_piece_at(move.from_square)
                    if test_piece is not None:
                        # Сохраняем взятие (если есть)
                        captured = test_board.get_piece_at(move.to_square)

                        # Перемещаем фигуру
                        test_board.squares[move.to_square] = test_piece
                        test_board.squares[move.from_square] = None

                        # Проверяем, не остался ли король под шахом
                        if not test_board.is_in_check(color):
                            legal_moves.append(move)

        return legal_moves

    def make_move(self, move):
        """Выполнение хода. Возвращает True, если ход был выполнен успешно"""
        piece = self.get_piece_at(move.from_square)
        if piece is None or piece.color.value != self.current_turn.value:
            return False

        # Проверяем, является ли ход легальным
        legal_moves = self.get_legal_moves(self.current_turn)
        if move not in legal_moves:
            return False

        # Сохраняем информацию о взятии (если есть)
        captured_piece = self.get_piece_at(move.to_square)

        # Выполняем рокировку
        if isinstance(piece, King) and abs(move.from_square.file - move.to_square.file) == 2:
            # Короткая рокировка
            if move.to_square.file == 6:
                rook_from = Square(7, move.from_square.rank)
                rook_to = Square(5, move.from_square.rank)
                rook = self.get_piece_at(rook_from)
                if rook is not None:
                    self.squares[rook_to] = rook
                    self.squares[rook_from] = None
                    rook.has_moved = True
            # Длинная рокировка
            elif move.to_square.file == 2:
                rook_from = Square(0, move.from_square.rank)
                rook_to = Square(3, move.from_square.rank)
                rook = self.get_piece_at(rook_from)
                if rook is not None:
                    self.squares[rook_to] = rook
                    self.squares[rook_from] = None
                    rook.has_moved = True

        # Превращение пешки
        if isinstance(piece, Pawn) and move.promotion:
            promotion_map = {
                'Q': Queen,
                'R': Rook,
                'B': Bishop,
                'N': Knight
            }
            if move.promotion in promotion_map:
                piece = promotion_map[move.promotion](piece.color)

        # Перемещаем фигуру
        self.squares[move.to_square] = piece
        self.squares[move.from_square] = None

        # Обновляем флаг has_moved
        piece.has_moved = True

        # Обновляем цель для взятия на проходе
        self.en_passant_target = None

        # Обновляем права на рокировку
        if isinstance(piece, King):
            self.castling_rights[piece.color]['king_side'] = False
            self.castling_rights[piece.color]['queen_side'] = False
        elif isinstance(piece, Rook):
            if move.from_square.file == 0:
                self.castling_rights[piece.color]['queen_side'] = False
            elif move.from_square.file == 7:
                self.castling_rights[piece.color]['king_side'] = False

        # Сохраняем ход в истории
        self.move_history.append((move, captured_piece))

        # Меняем очередь хода
        self.current_turn = self.current_turn.opposite()

        return True

    def undo_move(self):
        """Отмена последнего хода"""
        if not self.move_history:
            return False

        move, captured_piece = self.move_history.pop()

        # Возвращаем очередь хода
        self.current_turn = self.current_turn.opposite()

        # Получаем фигуру, которая сделала ход
        piece = self.get_piece_at(move.to_square)
        if piece is None:
            return False

        # Отмена рокировки
        if isinstance(piece, King) and abs(move.from_square.file - move.to_square.file) == 2:
            # Короткая рокировка
            if move.to_square.file == 6:
                rook_from = Square(5, move.from_square.rank)
                rook_to = Square(7, move.from_square.rank)
                rook = self.get_piece_at(rook_from)
                if rook is not None:
                    self.squares[rook_to] = rook
                    self.squares[rook_from] = None
                    rook.has_moved = False
            # Длинная рокировка
            elif move.to_square.file == 2:
                rook_from = Square(3, move.from_square.rank)
                rook_to = Square(0, move.from_square.rank)
                rook = self.get_piece_at(rook_from)
                if rook is not None:
                    self.squares[rook_to] = rook
                    self.squares[rook_from] = None
                    rook.has_moved = False

        # Отмена превращения пешки
        if isinstance(piece, Pawn) and move.promotion:
            piece = Pawn(piece.color)

        # Возвращаем фигуру на исходную позицию
        self.squares[move.from_square] = piece
        self.squares[move.to_square] = captured_piece

        return True

    def is_checkmate(self):
        """Проверка на мат"""
        if not self.is_in_check(self.current_turn):
            return False

        return len(self.get_legal_moves(self.current_turn)) == 0

    def is_stalemate(self):
        """Проверка на пат"""
        if self.is_in_check(self.current_turn):
            return False

        return len(self.get_legal_moves(self.current_turn)) == 0

    def is_insufficient_material(self):
        """Проверка на недостаточность материала"""
        pieces = []
        for piece in self.squares.values():
            if piece is not None:
                pieces.append(piece)

        # Только короли
        if len(pieces) == 2:
            return True

        # Король + слон/конь против короля
        if len(pieces) == 3:
            for piece in pieces:
                if isinstance(piece, (Bishop, Knight)):
                    return True

        return False

    def copy(self):
        """Создание копии доски"""
        new_board = Board()
        new_board.squares = {square: piece for square, piece in self.squares.items()}
        new_board.current_turn = Color(self.current_turn.value)
        new_board.move_history = self.move_history[:]
        new_board.castling_rights = {}
        for color, rights in self.castling_rights.items():
            new_board.castling_rights[Color(color.value)] = rights.copy()
        new_board.en_passant_target = self.en_passant_target
        return new_board

    def __str__(self):
        """Текстовое представление доски"""
        result = "\n    A    B    C    D    E    F    G    H\n"
        result += "  +" + "----+" * 8 + "\n"

        for rank in range(7, -1, -1):
            result += f"{rank + 1} |"
            for file in range(8):
                square = Square(file, rank)
                piece = self.get_piece_at(square)
                if piece:
                    result += f" {piece}  |"
                else:
                    result += "    |"
            result += f" {rank + 1}\n"
            result += "  +" + "----+" * 8 + "\n"

        result += "    A    B    C    D    E    F    G    H\n"
        return result


class Game:
    """Класс для управления игрой"""

    def __init__(self):
        self.board = Board()
        self.game_history = [self.board.copy()]
        self.current_move_index = 0
        self.is_review_mode = False

    def print_board(self):
        """Вывод доски на экран"""
        print(str(self.board))

    def show_legal_moves(self, color=None):
        """Показать все легальные ходы"""
        if color is None:
            color = self.board.current_turn

        try:
            moves = self.board.get_legal_moves(color)
            print(f"Доступные ходы ({len(moves)}):")

            if moves:
                for i, move in enumerate(moves):
                    print(f"  {i + 1:2d}. {move}", end="\n" if (i + 1) % 6 == 0 else "  ")
                if len(moves) % 6 != 0:
                    print()
            else:
                print("  Нет доступных ходов")
        except Exception as e:
            print(f"Ошибка при получении доступных ходов: {e}")

    def show_available_moves(self, square_str):
        """Показать доступные ходы для фигуры на указанной клетке"""
        try:
            square = Square.from_string(square_str)
            piece = self.board.get_piece_at(square)

            if piece is None:
                print(f"На поле {square_str.upper()} нет фигуры!")
                return

            if piece.color.value != self.board.current_turn.value:
                print(f"Фигура на поле {square_str.upper()} принадлежит противнику!")
                return

            moves = []
            for move in self.board.get_legal_moves(piece.color):
                if move.from_square == square:
                    moves.append(move)

            if not moves:
                print(f"У фигуры на {square_str.upper()} нет доступных ходов!")
                return

            print(f"Доступные ходы для {piece.get_display_name()} на {square_str.upper()}:")
            for i, move in enumerate(moves):
                print(f"  {i + 1:2d}. {move}", end="\n" if (i + 1) % 6 == 0 else "  ")
            if len(moves) % 6 != 0:
                print()

        except ValueError as e:
            print(f"Ошибка: {e}")

    def show_threatened_pieces(self):
        """Показать фигуры, находящиеся под угрозой"""
        threatened_pieces = []

        for square, piece in self.board.squares.items():
            if piece is not None and piece.color.value == self.board.current_turn.value:
                if self.board.is_square_attacked(square, piece.color.opposite()):
                    threatened_pieces.append((square, piece))

        if not threatened_pieces:
            print(f"У {self.board.current_turn} нет фигур под угрозой")
        else:
            print(f"Фигуры {self.board.current_turn} под угрозой:")
            for square, piece in threatened_pieces:
                attackers = []
                for from_square, attacker in self.board.squares.items():
                    if attacker is not None and attacker.color.value != piece.color.value:
                        attacked_squares = attacker.get_attacked_squares(self.board, from_square)
                        if square in attacked_squares:
                            attackers.append(attacker.get_display_name())

                print(f"  - {piece.get_display_name()} на {square} (угрожают: {', '.join(attackers)})")

        if self.board.is_in_check(self.board.current_turn):
            print(f"Внимание! Шах {self.board.current_turn} королю!")

    def handle_move_input(self, move_str):
        """Обработка ввода хода. Возвращает True если нужно выйти из игры"""
        move_str = move_str.strip()

        if move_str.lower() in ['?', 'help', 'помощь']:
            self.show_help()
            return False

        elif move_str.startswith('moves '):
            square = move_str[6:].strip()
            if square:
                self.show_available_moves(square)
            return False

        elif move_str == 'threats':
            self.show_threatened_pieces()
            return False

        elif move_str == 'legal':
            self.show_legal_moves()
            return False

        elif move_str == 'back':
            if self.board.undo_move():
                print("Отменили последний ход")
                self.print_board()
            else:
                print("Нельзя отменить ход")
            return False

        elif move_str.startswith('back '):
            try:
                num = int(move_str.split()[1])
                success = True
                for _ in range(num):
                    if not self.board.undo_move():
                        success = False
                        break

                if success:
                    print(f"Отменили {num} ходов")
                    self.print_board()
                else:
                    print("Нельзя отменить столько ходов")
            except ValueError:
                print("Используйте: back или back X (где X - число ходов)")
            return False

        elif move_str == 'save':
            self.save_game()
            return False

        elif move_str == 'load':
            self.load_game()
            return False

        elif move_str == 'review':
            self.enter_review_mode()
            return False

        elif move_str == 'play':
            self.exit_review_mode()
            return False

        elif move_str == 'exit':
            print("Игра завершена.")
            return True

        else:
            # Пробуем выполнить ход
            try:
                move = Move.from_string(move_str)
                if self.board.make_move(move):
                    print(f"Ход выполнен: {move}")
                    return False  # Не выходим из игры, просто успешный ход
                else:
                    print("Неверный ход! Используйте ? для помощи")
                    self.show_legal_moves()
                    return False
            except ValueError:
                print(f"Некорректный формат хода: {move_str}")
                return False

    def show_help(self):
        """Показать справку по командам"""
        print("""
Доступные команды:
  ? или help или помощь        - показать эту справку
  moves [поле]                - показать ходы фигуры (пример: moves e2)
  threats                     - показать фигуры под угрозой
  legal                       - показать все возможные ходы
  back                        - отменить последний ход
  back [число]                - отменить несколько ходов (пример: back 3)
  save                        - сохранить текущую партию
  load                        - загрузить партию из файла
  review                      - перейти в режим просмотра
  play                        - перейти в режим игры
  exit                        - выйти из игры

Формат ходов:
  e2e4                        - ход пешки с e2 на e4
  e7e8=Q                      - превращение пешки в ферзя
  e1g1                        - короткая рокировка белых
  e1c1                        - длинная рокировка белых
        """)

    def save_game(self):
        """Сохранение игры в файл"""
        filename = None
        try:
            filename = input("Введите имя файла для сохранения: ").strip()
            if not filename:
                print("Имя файла не может быть пустым!")
                return

            if not filename.endswith('.chess'):
                filename += '.chess'

            with open(filename, 'wb') as f:
                pickle.dump({
                    'board': self.board,
                    'current_index': self.current_move_index
                }, f)

            print(f"Игра сохранена в файл: {filename}")

        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def load_game(self):
        """Загрузка игры из файла"""
        filename = None
        try:
            filename = input("Введите имя файла для загрузки: ").strip()
            if not filename:
                print("Имя файла не может быть пустым!")
                return

            if not filename.endswith('.chess'):
                filename += '.chess'

            with open(filename, 'rb') as f:
                data = pickle.load(f)

            self.board = data['board']
            self.current_move_index = data['current_index']

            print(f"Игра загружена из файла: {filename}")
            self.print_board()

        except FileNotFoundError:
            print(f"Файл {filename} не найден!")
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")

    def enter_review_mode(self):
        """Вход в режим просмотра"""
        self.is_review_mode = True
        print("\n" + "=" * 50)
        print("РЕЖИМ ПРОСМОТРА ПАРТИИ")
        print("=" * 50)
        print("Команды: prev, next, first, last, play")
        self.print_board()

    def exit_review_mode(self):
        """Выход из режима просмотра"""
        self.is_review_mode = False
        print("\nВозврат к обычному режиму игры")
        self.print_board()

    def review_previous(self):
        """Переход к предыдущему ходу в режиме просмотра"""
        if self.board.undo_move():
            print("Перешли к предыдущему ходу")
            self.print_board()
        else:
            print("Это начало партии")

    def review_next(self):
        """Переход к следующему ходу в режиме просмотра"""
        print("Режим просмотра истории пока не реализован полностью")

    def review_first(self):
        """Переход к началу партии"""
        print("Режим просмотра истории пока не реализован полностью")

    def review_last(self):
        """Переход к концу партии"""
        print("Режим просмотра истории пока не реализован полностью")

    def play(self):
        """Основной игровой цикл"""
        print("=" * 50)
        print("ШАХМАТЫ")
        print("=" * 50)
        print("Введите ? для помощи\n")

        self.print_board()

        game_over = False

        while not game_over:
            # Проверка условий окончания игры
            if self.board.is_checkmate():
                winner = self.board.current_turn.opposite()
                print(f"\nШАХ И МАТ! Победили {winner}!")
                game_over = True
                continue

            if self.board.is_stalemate():
                print("\nПАТ! Ничья!")
                game_over = True
                continue

            if self.board.is_insufficient_material():
                print("\nНедостаточно материала для победы. Ничья!")
                game_over = True
                continue

            # Отображение текущего состояния
            print(f"\nХодят {self.board.current_turn}")
            if self.board.is_in_check(self.board.current_turn):
                print("ШАХ!")

            # Получение ввода от пользователя
            if self.is_review_mode:
                command = input(f"Просмотр [help для помощи]: ").strip()

                if command == 'prev':
                    self.review_previous()
                elif command == 'next':
                    self.review_next()
                elif command == 'first':
                    self.review_first()
                elif command == 'last':
                    self.review_last()
                elif command == 'play':
                    self.exit_review_mode()
                elif command == 'exit':
                    break
                else:
                    self.handle_move_input(command)
            else:
                command = input(f"Введите ход или команду: ").strip()

                if command in ['prev', 'next', 'first', 'last']:
                    print("Эти команды доступны только в режиме просмотра (review)")
                    continue

                exit_game = self.handle_move_input(command)
                if exit_game:
                    break

                # Если ход был выполнен успешно, показываем доску
                if command not in ['?', 'help', 'помощь', 'moves', 'threats', 'legal', 'back', 'save', 'load', 'review',
                                   'play']:
                    self.print_board()

        # После окончания игры предлагаем сыграть еще раз
        if game_over:
            while True:
                again = input("\nСыграть еще раз? (да/нет): ").strip().lower()
                if again in ['да', 'yes', 'y', 'д']:
                    self.__init__()  # Сбрасываем игру
                    self.play()
                    break
                elif again in ['нет', 'no', 'n', 'н']:
                    print("Спасибо за игру!")
                    break
                else:
                    print("Введите 'да' или 'нет'")


def main():
    """Точка входа в программу"""
    game = Game()
    game.play()


if __name__ == "__main__":
    main()