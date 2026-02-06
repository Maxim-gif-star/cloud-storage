import pygame
import chess
import random
import sys

pygame.init()


class MinMaxBot:
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
        if board.is_checkmate():
            return -100000 if board.turn else 100000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value
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
        score += len(list(board.legal_moves)) * 5 * (1 if board.turn else -1)
        king_square = board.king(board.turn)
        if king_square:
            file, rank = chess.square_file(king_square), chess.square_rank(king_square)
            if rank == (0 if board.turn else 7):
                score += -30 * (1 if board.turn else -1)
            elif file in [0, 7] or rank in [0, 7]:
                score += -20 * (1 if board.turn else -1)
        if board.is_check():
            score += -50 * (1 if board.turn else -1)
        return score

    def minimax(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
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
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise Exception("Нет возможных ходов")
        best_move = None
        best_value = -float('inf')
        depth = 3
        for move in legal_moves:
            board.push(move)
            move_value = self.minimax(board, depth - 1, -float('inf'), float('inf'), False)
            board.pop()
            if move_value > best_value:
                best_value = move_value
                best_move = move
            elif move_value == best_value and random.random() > 0.5:
                best_move = move
        return best_move


class ChessPygame:
    def __init__(self):
        self.board = chess.Board()
        self.bot_white = MinMaxBot()
        self.bot_black = MinMaxBot()
        self.screen_size = 400
        self.cell_size = self.screen_size // 8
        self.screen = pygame.display.set_mode((self.screen_size, self.screen_size + 150))
        pygame.display.set_caption("Шахматы - Бот против Бота")
        self.font = pygame.font.SysFont('Arial', 24)
        self.small_font = pygame.font.SysFont('Arial', 20)
        self.piece_font = pygame.font.SysFont('Segoe UI Symbol', 40)
        self.move_count = 1
        self.game_over = False
        self.message = ""
        self.info_text = ""
        self.piece_symbols = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
        }

        # ЦВЕТА КЛЕТОК (БОЛЕЕ ТЕМНЫЕ)

        self.light_color = (210, 180, 140)  # Рыжий/бежевый/коричневый
        self.dark_color = (50, 50, 50)
        # Стандартные: (238, 238, 210) и (118, 150, 86)
        # Более темные варианты:
        # self.light_color = (10, 200, 170)  # Было (238, 238, 210)
        # self.dark_color = (10, 120, 60)  # Было (118, 150, 86)

        # Другие варианты темных цветов (раскомментируйте нужный):
        # self.light_color = (220, 220, 180)   # Светло-бежевый
        # self.dark_color = (70, 110, 50)      # Темно-зеленый

        # self.light_color = (210, 210, 170)   # Бежевый
        # self.dark_color = (90, 130, 70)      # Зеленый

        # self.light_color = (230, 230, 190)   # Очень светлый
        # self.dark_color = (100, 140, 80)     # Средний зеленый

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                color = self.light_color if (row + col) % 2 == 0 else self.dark_color
                pygame.draw.rect(self.screen, color,
                                 (col * self.cell_size, row * self.cell_size,
                                  self.cell_size, self.cell_size))

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                piece_symbol = piece.symbol()
                row, col = 7 - chess.square_rank(square), chess.square_file(square)

                piece_char = self.piece_symbols.get(piece_symbol, piece_symbol)
                piece_color = (30, 30, 30) if piece_symbol.islower() else (245, 245, 245)

                # Добавляем легкую тень для лучшей читаемости на темных клетках
                if (row + col) % 2 == 1:  # На темных клетках
                    shadow_surface = self.piece_font.render(piece_char, True, (10, 10, 10))
                    shadow_rect = shadow_surface.get_rect(center=(
                        col * self.cell_size + self.cell_size // 2 + 1,
                        row * self.cell_size + self.cell_size // 2 + 1
                    ))
                    self.screen.blit(shadow_surface, shadow_rect)

                piece_surface = self.piece_font.render(piece_char, True, piece_color)
                piece_rect = piece_surface.get_rect(center=(
                    col * self.cell_size + self.cell_size // 2,
                    row * self.cell_size + self.cell_size // 2
                ))
                self.screen.blit(piece_surface, piece_rect)

        # Рисуем линии сетки
        for i in range(9):
            line_color = (40, 40, 40)
            pygame.draw.line(self.screen, line_color,
                             (i * self.cell_size, 0),
                             (i * self.cell_size, self.screen_size), 1)
            pygame.draw.line(self.screen, line_color,
                             (0, i * self.cell_size),
                             (self.screen_size, i * self.cell_size), 1)

        # Подписи координат
        for i in range(8):
            file_label = chr(ord('a') + i)
            rank_label = str(8 - i)

            # Для светлых клеток - темный текст, для темных клеток - светлый текст
            file_color = (60, 60, 60) if i % 2 == 0 else (220, 220, 220)
            rank_color = (60, 60, 60) if (7 - i) % 2 == 0 else (220, 220, 220)

            file_surface = self.small_font.render(file_label, True, file_color)
            rank_surface = self.small_font.render(rank_label, True, rank_color)

            # Буквы снизу
            self.screen.blit(file_surface, (i * self.cell_size + 5, self.screen_size - 20))
            # Буквы сверху
            self.screen.blit(file_surface, (i * self.cell_size + 5, 5))
            # Цифры слева
            self.screen.blit(rank_surface, (5, i * self.cell_size + 5))
            # Цифры справа
            self.screen.blit(rank_surface, (self.screen_size - 20, i * self.cell_size + 5))

    def draw_info(self):
        info_y = self.screen_size + 10
        pygame.draw.rect(self.screen, (50, 50, 50), (0, self.screen_size, self.screen_size, 120))

        turn_text = "Ход: Белые (Бот 1)" if self.board.turn else "Ход: Черные (Бот 2)"
        turn_surface = self.font.render(turn_text, True, (255, 255, 255))
        self.screen.blit(turn_surface, (10, info_y))

        move_text = f"Ход №: {self.move_count}"
        move_surface = self.font.render(move_text, True, (255, 255, 255))
        self.screen.blit(move_surface, (self.screen_size - 150, info_y))

        if self.message:
            msg_surface = self.font.render(self.message, True, (255, 215, 0))
            self.screen.blit(msg_surface, (10, info_y + 35))

        if self.info_text:
            info_surface = self.small_font.render(self.info_text, True, (200, 200, 200))
            self.screen.blit(info_surface, (10, info_y + 70))

        if self.game_over:
            restart_text = self.small_font.render("Нажмите R для новой игры, ESC для выхода", True, (255, 255, 255))
            self.screen.blit(restart_text, (self.screen_size // 2 - restart_text.get_width() // 2, info_y + 95))

    def check_game_status(self):
        if self.board.is_checkmate():
            self.message = f"МАТ! Победили {'белые' if not self.board.turn else 'черные'}!"
            self.game_over = True
            return True
        elif self.board.is_stalemate():
            self.message = "ПАТ - НИЧЬЯ!"
            self.game_over = True
            return True
        elif self.board.is_insufficient_material():
            self.message = "НЕДОСТАТОЧНО МАТЕРИАЛА - НИЧЬЯ!"
            self.game_over = True
            return True
        elif self.board.is_check():
            self.info_text = "ШАХ!"
        else:
            self.info_text = ""
        return False

    def run(self):
        clock = pygame.time.Clock()
        bot_thinking = False

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.__init__()
                        continue
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            if not self.game_over and not bot_thinking:
                bot_thinking = True
                pygame.time.set_timer(pygame.USEREVENT, 500)

            self.screen.fill((40, 40, 40))
            self.draw_board()
            self.draw_info()

            if bot_thinking and not self.game_over:
                try:
                    current_bot = self.bot_white if self.board.turn else self.bot_black
                    move = current_bot.get_move(self.board)
                    self.board.push(move)

                    try:
                        san_move = self.board.san(move)
                        self.info_text = f"Ход {self.move_count}: {san_move}"
                    except:
                        self.info_text = f"Ход {self.move_count}: {move}"

                    self.move_count += 1
                    self.check_game_status()
                except Exception as e:
                    self.message = f"Ошибка: {e}"
                    self.game_over = True

                bot_thinking = False
                pygame.time.set_timer(pygame.USEREVENT, 0)

            pygame.display.flip()
            clock.tick(30)


if __name__ == "__main__":
    game = ChessPygame()
    game.run()