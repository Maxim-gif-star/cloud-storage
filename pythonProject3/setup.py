from cx_Freeze import setup, Executable

setup(
    name="ChessBot",
    version="1.0",
    description="Шахматный бот",
    executables=[Executable("chess_pygame.py", base="Win32GUI")]
)