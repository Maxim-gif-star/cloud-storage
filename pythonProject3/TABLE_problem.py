from typing import List, Dict, Any, Union, Optional
from datetime import datetime
import copy


class TableEditor:
    def __init__(self):
        self.data: List[List[Any]] = []
        self.column_types: Dict[Union[int, str], type] = {}
        self.column_names: List[str] = []
        self.filename = None

    def _convert_value(self, value: Any, col_type: type) -> Any:
        """Конвертирует значение к указанному типу"""
        if value is None or value == '':
            return None

        try:
            if col_type == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'y')
                return bool(value)
            elif col_type == datetime:
                if isinstance(value, str):
                    return datetime.fromisoformat(value)
                return value
            else:
                return col_type(value)
        except (ValueError, TypeError):
            return None

    def _get_column_identifier(self, column: Union[int, str]) -> int:
        """Получает числовой идентификатор столбца"""
        if isinstance(column, int):
            if 0 <= column < len(self.column_names):
                return column
            raise IndexError(f"Column index {column} out of range")
        elif isinstance(column, str):
            if column in self.column_names:
                return self.column_names.index(column)
            raise ValueError(f"Column '{column}' not found")
        else:
            raise TypeError("Column must be int or str")

    # Основные методы из задания
    def get_rows_by_number(self, start: int, stop: Optional[int] = None, copy_table: bool = False):
        """Получение строк по номерам"""
        if not self.data:
            raise ValueError("Table is empty")

        if stop is None:
            stop = start + 1

        if start < 0 or stop > len(self.data) or start >= stop:
            raise IndexError("Invalid row range")

        result = TableEditor()
        result.column_names = self.column_names.copy()
        result.column_types = self.column_types.copy()

        if copy_table:
            result.data = copy.deepcopy(self.data[start:stop])
        else:
            result.data = self.data[start:stop]

        return result

    def get_rows_by_index(self, *values: Any, copy_table: bool = False):
        """Получение строк по значениям в первом столбце"""
        if not self.data:
            raise ValueError("Table is empty")

        result = TableEditor()
        result.column_names = self.column_names.copy()
        result.column_types = self.column_types.copy()

        target_values = set(values)
        if copy_table:
            result.data = [copy.deepcopy(row) for row in self.data
                           if row and row[0] in target_values]
        else:
            result.data = [row for row in self.data
                           if row and row[0] in target_values]

        return result

    def get_column_types(self, by_number: bool = True) -> Dict[Union[int, str], type]:
        """Получение типов столбцов"""
        if by_number:
            return {i: self.column_types.get(i, str) for i in range(len(self.column_names))}
        else:
            return {name: self.column_types.get(i, str)
                    for i, name in enumerate(self.column_names)}

    def set_column_types(self, types_dict: Dict[Union[int, str], type], by_number: bool = True):
        """Установка типов столбцов"""
        for col, col_type in types_dict.items():
            if by_number:
                col_idx = col if isinstance(col, int) else self._get_column_identifier(col)
            else:
                col_idx = self._get_column_identifier(col)

            if col_type not in (int, float, bool, str, datetime):
                raise ValueError(f"Unsupported type: {col_type}")

            self.column_types[col_idx] = col_type

            # Конвертируем существующие данные
            for row in self.data:
                if row and col_idx < len(row):
                    row[col_idx] = self._convert_value(row[col_idx], col_type)

    def get_values(self, column: Union[int, str] = 0) -> List[Any]:
        """Получение значений столбца"""
        col_idx = self._get_column_identifier(column)
        col_type = self.column_types.get(col_idx, str)

        return [self._convert_value(row[col_idx], col_type) if row and col_idx < len(row) else None
                for row in self.data]

    def get_value(self, column: Union[int, str] = 0) -> Any:
        """Получение значения для таблицы с одной строкой"""
        if len(self.data) != 1:
            raise ValueError("This method works only for single-row tables")
        return self.get_values(column)[0]

    def set_values(self, values: List[Any], column: Union[int, str] = 0):
        """Установка значений столбца"""
        if len(values) != len(self.data):
            raise ValueError("Values length must match number of rows")

        col_idx = self._get_column_identifier(column)
        col_type = self.column_types.get(col_idx, str)

        for i, value in enumerate(values):
            if i < len(self.data) and self.data[i]:
                if col_idx < len(self.data[i]):
                    self.data[i][col_idx] = self._convert_value(value, col_type)
                else:
                    # Расширяем строку если нужно
                    self.data[i].extend([None] * (col_idx - len(self.data[i]) + 1))
                    self.data[i][col_idx] = self._convert_value(value, col_type)

    def set_value(self, value: Any, column: Union[int, str] = 0):
        """Установка значения для таблицы с одной строкой"""
        if len(self.data) != 1:
            raise ValueError("This method works only for single-row tables")
        self.set_values([value], column)

    def print_table(self):
        """Вывод таблицы"""
        if not self.data:
            print("Empty table")
            return

        # Определяем ширину столбцов
        col_widths = []
        for i in range(len(self.column_names)):
            max_width = len(str(self.column_names[i]))
            for row in self.data:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width + 2)

        # Заголовок
        header = " | ".join(f"{name:<{col_widths[i]}}"
                            for i, name in enumerate(self.column_names))
        print(header)
        print("-" * len(header))

        # Данные
        for row in self.data:
            row_str = " | ".join(f"{str(cell if cell is not None else 'NULL'):<{col_widths[i]}}"
                                 for i, cell in enumerate(row) if i < len(col_widths))
            print(row_str)

    # Дополнительные методы
    def auto_detect_types(self):
        """Автоматическое определение типов столбцов"""
        if not self.data:
            return

        for col_idx in range(len(self.column_names)):
            values = [row[col_idx] for row in self.data if row and col_idx < len(row) and row[col_idx] is not None]
            if not values:
                self.column_types[col_idx] = str
                continue

            # Пробуем определить тип
            detected_type = str
            for test_type in [int, float, datetime, bool]:
                try:
                    for val in values:
                        self._convert_value(val, test_type)
                    detected_type = test_type
                    break
                except (ValueError, TypeError):
                    continue

            self.column_types[col_idx] = detected_type

    def add(self, col1: Union[int, str], col2: Union[int, str], result_col: Union[int, str]):
        """Сложение столбцов"""
        self._arithmetic_operation(col1, col2, result_col, lambda x, y: x + y)

    def sub(self, col1: Union[int, str], col2: Union[int, str], result_col: Union[int, str]):
        """Вычитание столбцов"""
        self._arithmetic_operation(col1, col2, result_col, lambda x, y: x - y)

    def mul(self, col1: Union[int, str], col2: Union[int, str], result_col: Union[int, str]):
        """Умножение столбцов"""
        self._arithmetic_operation(col1, col2, result_col, lambda x, y: x * y)

    def div(self, col1: Union[int, str], col2: Union[int, str], result_col: Union[int, str]):
        """Деление столбцов"""
        self._arithmetic_operation(col1, col2, result_col, lambda x, y: x / y if y != 0 else None)

    def _arithmetic_operation(self, col1: Union[int, str], col2: Union[int, str],
                              result_col: Union[int, str], operation):
        """Вспомогательный метод для арифметических операций"""
        col1_idx = self._get_column_identifier(col1)
        col2_idx = self._get_column_identifier(col2)
        result_idx = self._get_column_identifier(result_col)

        col1_type = self.column_types.get(col1_idx, str)
        col2_type = self.column_types.get(col2_idx, str)

        if col1_type not in (int, float, bool) or col2_type not in (int, float, bool):
            raise TypeError("Arithmetic operations supported only for numeric columns")

        values1 = self.get_values(col1_idx)
        values2 = self.get_values(col2_idx)

        result_values = []
        for v1, v2 in zip(values1, values2):
            if v1 is None or v2 is None:
                result_values.append(None)
            else:
                try:
                    result_values.append(operation(v1, v2))
                except (TypeError, ZeroDivisionError):
                    result_values.append(None)

        self.set_values(result_values, result_idx)
        self.column_types[result_idx] = float  # Результат обычно float

    def filter_rows(self, bool_list: List[bool], copy_table: bool = False):
        """Фильтрация строк по булеву списку"""
        if len(bool_list) != len(self.data):
            raise ValueError("Boolean list length must match number of rows")

        result = TableEditor()
        result.column_names = self.column_names.copy()
        result.column_types = self.column_types.copy()

        if copy_table:
            result.data = [copy.deepcopy(self.data[i]) for i, keep in enumerate(bool_list) if keep]
        else:
            result.data = [self.data[i] for i, keep in enumerate(bool_list) if keep]

        return result