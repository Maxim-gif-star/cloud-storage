import pandas as pd
import pickle
import csv
import os
from datetime import datetime


class Table:
    def __init__(self):
        self.table = {}
        self.column_types = {}
        self.column_names = []

    def _validate_column(self, column):
        if isinstance(column, int):
            if column < 0 or column >= len(self.column_names):
                raise ValueError(f"Некорректный номер столбца: {column}")
            return self.column_names[column]
        elif isinstance(column, str):
            if column not in self.column_names:
                raise ValueError(f"Столбец '{column}' не существует")
            return column
        else:
            raise TypeError("Столбец должен быть int или str")

    def _convert_value(self, value, target_type):
        if value is None:
            return None

        try:
            if target_type == 'int':
                return int(value)
            elif target_type == 'float':
                return float(value)
            elif target_type == 'bool':
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'y')
                return bool(value)
            elif target_type == 'datetime':
                if isinstance(value, str):
                    return datetime.fromisoformat(value)
                return value
            else:
                return str(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Ошибка конвертации {value} в {target_type}: {e}")

    def _auto_detect_type(self, values):
        if not values:
            return 'str'

        non_none_values = [v for v in values if v is not None]
        if not non_none_values:
            return 'str'

        datetime_count = 0
        for val in non_none_values:
            try:
                if isinstance(val, str):
                    datetime.fromisoformat(val)
                    datetime_count += 1
            except:
                pass

        if datetime_count / len(non_none_values) > 0.8:
            return 'datetime'

        try:
            [int(v) for v in non_none_values]
            return 'int'
        except:
            pass

        try:
            [float(v) for v in non_none_values]
            return 'float'
        except:
            pass

        bool_count = 0
        for val in non_none_values:
            if str(val).lower() in ('true', 'false', '1', '0', 'yes', 'no'):
                bool_count += 1

        if bool_count / len(non_none_values) > 0.8:
            return 'bool'

        return 'str'

    def _auto_detect_column_types(self, df=None):
        if df is None:
            df = pd.DataFrame(self.table)

        for col in df.columns:
            values = df[col].tolist()
            self.column_types[col] = self._auto_detect_type(values)

    def Check_Convert_Types(self, values, column):
        col_type = self.column_types.get(column, 'str')
        return [self._convert_value(v, col_type) for v in values]

    def _assign_result(self, column, result):
        self.table[column] = self.Check_Convert_Types(result, column)

    def _arithmetic_operation(self, column1, column2, operation):
        if column1 not in self.table or column2 not in self.table:
            raise ValueError("Один из столбцов не существует")

        col1_type = self.column_types.get(column1, 'str')
        col2_type = self.column_types.get(column2, 'str')

        if col1_type not in ('int', 'float', 'bool') or col2_type not in ('int', 'float', 'bool'):
            raise TypeError("Арифметические операции поддерживаются только для числовых типов")

        values1 = self.table[column1]
        values2 = self.table[column2]

        if len(values1) != len(values2):
            raise ValueError("Столбцы должны иметь одинаковую длину")

        result = []
        for v1, v2 in zip(values1, values2):
            if v1 is None or v2 is None:
                result.append(None)
                continue

            try:
                if operation == 'add':
                    result.append(v1 + v2)
                elif operation == 'sub':
                    result.append(v1 - v2)
                elif operation == 'mul':
                    result.append(v1 * v2)
                elif operation == 'div':
                    if v2 == 0:
                        result.append(None)
                    else:
                        result.append(v1 / v2)
            except TypeError as e:
                raise TypeError(f"Невозможно выполнить операцию {operation} для {v1} и {v2}: {e}")

        return result

    def _comparison_operation(self, column1, column2, operation):
        if column1 not in self.table or column2 not in self.table:
            raise ValueError("Один из столбцов не существует")

        values1 = self.table[column1]
        values2 = self.table[column2]

        if len(values1) != len(values2):
            raise ValueError("Столбцы должны иметь одинаковую длину")

        result = []
        for v1, v2 in zip(values1, values2):
            if v1 is None or v2 is None:
                result.append(False)
                continue

            try:
                if operation == 'eq':
                    result.append(v1 == v2)
                elif operation == 'gr':
                    result.append(v1 > v2)
                elif operation == 'ls':
                    result.append(v1 < v2)
                elif operation == 'ge':
                    result.append(v1 >= v2)
                elif operation == 'le':
                    result.append(v1 <= v2)
                elif operation == 'ne':
                    result.append(v1 != v2)
            except TypeError:
                result.append(False)

        return result

    def load_table(self, *files, auto_detect_types=True):
        if not files:
            raise ValueError("Не указаны файлы для загрузки")

        all_tables = []
        for file_path in files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл {file_path} не существует")

            if file_path.endswith('.csv'):
                table = self._load_csv(file_path)
            elif file_path.endswith('.pickle'):
                table = self._load_pickle(file_path)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {file_path}")

            all_tables.append(table)

        if len(all_tables) == 1:
            self.table = all_tables[0]
        else:
            self.table = self._merge_multiple_tables(all_tables)

        self.column_names = list(self.table.keys())

        if auto_detect_types:
            self._auto_detect_column_types()

    def _load_csv(self, file_path):
        table = {}
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return {}

            for field in reader.fieldnames:
                table[field] = []

            for row in reader:
                for field in reader.fieldnames:
                    value = row[field]
                    table[field].append(value if value != '' else None)

        return table

    def _load_pickle(self, file_path):
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        return data

    def _merge_multiple_tables(self, tables):
        if not tables:
            return {}

        first_columns = set(tables[0].keys())
        for i, table in enumerate(tables[1:], 1):
            if set(table.keys()) != first_columns:
                raise ValueError(f"Таблица {i} имеет несовместимую структуру столбцов")

        merged = {}
        for col in first_columns:
            merged[col] = []
            for table in tables:
                merged[col].extend(table[col])

        return merged

    def save_table(self, file_path, max_rows=None, **kwargs):
        if not self.table:
            raise ValueError("Таблица пуста")

        if file_path.endswith('.csv'):
            self._save_csv(file_path, max_rows, **kwargs)
        elif file_path.endswith('.pickle'):
            self._save_pickle(file_path, max_rows, **kwargs)
        elif file_path.endswith('.txt'):
            self._save_txt(file_path, **kwargs)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_path}")

    def _save_csv(self, file_path, max_rows=None, **kwargs):
        df = pd.DataFrame(self.table)

        if max_rows and len(df) > max_rows:
            base_name = file_path[:-4] if file_path.endswith('.csv') else file_path
            for i, start_idx in enumerate(range(0, len(df), max_rows)):
                part_df = df.iloc[start_idx:start_idx + max_rows]
                part_file = f"{base_name}_part{i + 1}.csv"
                part_df.to_csv(part_file, index=False, encoding='utf-8')
        else:
            df.to_csv(file_path, index=False, encoding='utf-8')

    def _save_pickle(self, file_path, max_rows=None, **kwargs):
        if max_rows and len(next(iter(self.table.values()))) > max_rows:
            base_name = file_path[:-7] if file_path.endswith('.pickle') else file_path
            df = pd.DataFrame(self.table)
            for i, start_idx in enumerate(range(0, len(df), max_rows)):
                part_table = {}
                for col in self.table:
                    part_table[col] = self.table[col][start_idx:start_idx + max_rows]
                part_file = f"{base_name}_part{i + 1}.pickle"
                with open(part_file, 'wb') as f:
                    pickle.dump(part_table, f)
        else:
            with open(file_path, 'wb') as f:
                pickle.dump(self.table, f)

    def _save_txt(self, file_path, **kwargs):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self._get_table_repr())

    def _get_table_repr(self):
        if not self.table:
            return "Пустая таблица"

        df = pd.DataFrame(self.table)
        return df.to_string(index=False)

    def get_rows_by_number(self, start, stop=None, copy_table=False):
        if not self.table:
            raise ValueError("Таблица пуста")

        df = pd.DataFrame(self.table)

        if stop is None:
            result_df = df.iloc[start:start + 1]
        else:
            if start >= stop:
                raise ValueError("Начальный индекс должен быть меньше конечного")
            result_df = df.iloc[start:stop + 1]

        result = Table()
        result.table = result_df.to_dict('list')
        result.column_names = self.column_names.copy()
        result.column_types = self.column_types.copy() if copy_table else self.column_types

        return result

    def get_rows_by_index(self, *values, copy_table=False):
        if not self.table:
            raise ValueError("Таблица пуста")

        if not values:
            raise ValueError("Не указаны значения для поиска")

        df = pd.DataFrame(self.table)
        index_col = df.columns[0]

        mask = df[index_col].isin(values)
        result_df = df[mask]

        result = Table()
        result.table = result_df.to_dict('list')
        result.column_names = self.column_names.copy()
        result.column_types = self.column_types.copy() if copy_table else self.column_types

        return result

    def get_column_types(self, by_number=True):
        if by_number:
            return {i: self.column_types.get(col, 'str')
                    for i, col in enumerate(self.column_names)}
        else:
            return self.column_types.copy()

    def set_column_types(self, types_dict, by_number=True):
        for key, type_name in types_dict.items():
            if by_number:
                if not isinstance(key, int) or key < 0 or key >= len(self.column_names):
                    raise ValueError(f"Некорректный номер столбца: {key}")
                col_name = self.column_names[key]
            else:
                if key not in self.column_names:
                    raise ValueError(f"Столбец '{key}' не существует")
                col_name = key

            if type_name not in ('int', 'float', 'bool', 'str', 'datetime'):
                raise ValueError(f"Неподдерживаемый тип: {type_name}")

            self.column_types[col_name] = type_name

            if col_name in self.table:
                self.table[col_name] = self.Check_Convert_Types(self.table[col_name], col_name)

    def get_values(self, column=0):
        col_name = self._validate_column(column)
        return self.table.get(col_name, [])

    def get_value(self, column=0):
        values = self.get_values(column)
        return values[0] if values else None

    def set_values(self, values, column=0):
        if not isinstance(values, list):
            raise TypeError("values должен быть списком")

        col_name = self._validate_column(column)

        if len(values) != len(next(iter(self.table.values()))):
            raise ValueError("Количество значений должно соответствовать количеству строк")

        self.table[col_name] = self.Check_Convert_Types(values, col_name)

    def set_value(self, value, column=0):
        col_name = self._validate_column(column)

        if self.table[col_name]:
            new_values = self.table[col_name].copy()
            new_values[0] = self._convert_value(value, self.column_types.get(col_name, 'str'))
            self.table[col_name] = new_values
        else:
            raise ValueError("Столбец пуст")

    def print_table(self):
        print(self._get_table_repr())

    def concat(self, table1, table2):
        dict1 = table1.table
        dict2 = table2.table

        df1 = pd.DataFrame(dict1)
        df2 = pd.DataFrame(dict2)

        if set(df1.columns) != set(df2.columns):
            raise ValueError("Таблицы имеют разные наборы столбцов")

        result_df = pd.concat([df1, df2], ignore_index=True)

        result = Table()
        result.table = result_df.to_dict('list')
        result.column_names = list(result.table.keys())
        result._auto_detect_column_types()

        return result

    def split(self, row_number):
        dict_table = self.table
        df = pd.DataFrame(dict_table)

        if row_number < 0 or row_number >= len(df):
            raise ValueError("Некорректный номер строки для разделения")

        df1 = df.iloc[:row_number]
        df2 = df.iloc[row_number:]

        table1 = Table()
        table1.table = df1.to_dict('list')
        table1.column_names = self.column_names.copy()
        table1.column_types = self.column_types.copy()

        table2 = Table()
        table2.table = df2.to_dict('list')
        table2.column_names = self.column_names.copy()
        table2.column_types = self.column_types.copy()

        return table1, table2

    def add(self, column1, column2):
        result = self._arithmetic_operation(column1, column2, 'add')
        self._assign_result(column1, result)

    def sub(self, column1, column2):
        result = self._arithmetic_operation(column1, column2, 'sub')
        self._assign_result(column1, result)

    def mul(self, column1, column2):
        result = self._arithmetic_operation(column1, column2, 'mul')
        self._assign_result(column1, result)

    def div(self, column1, column2):
        result = self._arithmetic_operation(column1, column2, 'div')
        self._assign_result(column1, result)

    def eq(self, column1, column2):
        return self._comparison_operation(column1, column2, 'eq')

    def gr(self, column1, column2):
        return self._comparison_operation(column1, column2, 'gr')

    def ls(self, column1, column2):
        return self._comparison_operation(column1, column2, 'ls')

    def ge(self, column1, column2):
        return self._comparison_operation(column1, column2, 'ge')

    def le(self, column1, column2):
        return self._comparison_operation(column1, column2, 'le')

    def ne(self, column1, column2):
        return self._comparison_operation(column1, column2, 'ne')

    def filter_rows(self, bool_list, copy_table=False):
        if not self.table:
            raise ValueError("Таблица пуста")

        if len(bool_list) != len(next(iter(self.table.values()))):
            raise ValueError("Длина bool_list должна соответствовать количеству строк")

        df = pd.DataFrame(self.table)
        result_df = df[bool_list]

        result = Table()
        result.table = result_df.to_dict('list')
        result.column_names = self.column_names.copy()
        result.column_types = self.column_types.copy() if copy_table else self.column_types

        return result

    def merge_tables(self, table1, table2, by_number=True, **kwargs):
        dict1 = table1.table
        dict2 = table2.table

        df1 = pd.DataFrame(dict1)
        df2 = pd.DataFrame(dict2)

        if by_number:
            if len(df1) != len(df2):
                raise ValueError("Таблицы должны иметь одинаковое количество строк для слияния по номерам")

            result_df = pd.concat([df1, df2], axis=1)
        else:
            index_col = df1.columns[0]
            if index_col not in df2.columns:
                raise ValueError(f"Столбец {index_col} не найден во второй таблице")

            result_df = pd.merge(df1, df2, on=index_col, how='outer')

        result_columns = []
        for col in result_df.columns:
            if col in df1.columns and col in df2.columns and col != index_col:
                result_columns.append(f"{col}_x")
                result_columns.append(f"{col}_y")
            else:
                result_columns.append(col)

        result_df.columns = result_columns

        result = Table()
        result.table = result_df.to_dict('list')
        result.column_names = list(result_df.columns)
        result._auto_detect_column_types(result_df)

        return result

    def save_table(self):
        return self.table.copy()

    def load_table_to_txt(self, inp, table_tp):
        pass

    def __len__(self):
        if not self.table:
            return 0
        return len(next(iter(self.table.values())))

    def __repr__(self):
        return f"Table(columns={len(self.column_names)}, rows={len(self)})"


def main():
    processor = Table()
    loaded_tables = []  # Список для хранения загруженных таблиц

    while True:
        print("\n" + "=" * 50)
        print("Введите номер функции (0-22):")
        print("0) Выход")
        print("1) Загрузить таблицу (load_table)")
        print("2) Сохранить таблицу (save_table)")
        print("3) get_rows_by_number")
        print("4) get_rows_by_index")
        print("5) get_column_types")
        print("6) set_column_types")
        print("7) get_values")
        print("8) get_value")
        print("9) set_values")
        print("10) set_value")
        print("11) print_table")
        print("12) Арифметические операции (add, sub, mul, div)")
        print("13) Операции сравнения (eq, gr, ls, ge, le, ne)")
        print("14) Фильтрация строк (filter_rows)")
        print("15) Объединение таблиц (concat)")
        print("16) Разделение таблицы (split)")
        print("17) Слияние таблиц (merge_tables)")
        print("18) Показать все загруженные таблицы")
        print("19) Выбрать активную таблицу")
        print("20) Создать новую таблицу")
        print("21) Удалить таблицу")
        print("22) Проверить состояние текущей таблицы")
        print("=" * 50)

        choice = input("Выберите функцию (0-22): ").strip()

        try:
            if choice == "0":
                print("Выход из программы.")
                break

            elif choice == "1":
                files = input("Введите пути к файлам через запятую: ").strip().split(',')
                files = [f.strip() for f in files if f.strip()]
                auto_detect = input("Автоматически определить типы? (y/n): ").strip().lower() == 'y'
                processor.load_table(*files, auto_detect_types=auto_detect)
                loaded_tables.append(processor.table.copy())
                print("Таблица успешно загружена")

            elif choice == "2":
                file_path = input("Введите путь для сохранения: ").strip()
                max_rows = input("Максимальное количество строк в файле (Enter для одного файла): ").strip()
                max_rows = int(max_rows) if max_rows else None
                processor.save_table(file_path, max_rows)
                print("Таблица успешно сохранена")

            elif choice == "3":
                print("1 - одна строка, 2 - интервал строк")
                sub_choice = input("Выберите вариант: ").strip()

                if sub_choice == "1":
                    start = int(input("Введите номер строки: "))
                    result = processor.get_rows_by_number(start)
                    result.print_table()
                elif sub_choice == "2":
                    start = int(input("Введите начальный номер: "))
                    stop = int(input("Введите конечный номер: "))
                    copy_table = input("Копировать таблицу? (y/n): ").strip().lower() == 'y'
                    result = processor.get_rows_by_number(start, stop, copy_table)
                    result.print_table()
                else:
                    print("Неверный выбор")

            elif choice == "4":
                print("1 - одно значение, 2 - несколько значений")
                sub_choice = input("Выберите вариант: ").strip()

                if sub_choice == "1":
                    value = input("Введите значение для поиска: ")
                    result = processor.get_rows_by_index(value)
                    result.print_table()
                elif sub_choice == "2":
                    values = input("Введите значения через запятую: ").split(',')
                    values = [v.strip() for v in values]
                    copy_table = input("Копировать таблицу? (y/n): ").strip().lower() == 'y'
                    result = processor.get_rows_by_index(*values, copy_table=copy_table)
                    result.print_table()
                else:
                    print("Неверный выбор")

            elif choice == "5":
                by_number = input("По номерам? (y/n): ").strip().lower() == 'y'
                types = processor.get_column_types(by_number)
                print("Типы столбцов:")
                for col, col_type in types.items():
                    print(f"  {col}: {col_type}")

            elif choice == "6":
                print("Формат: номер/имя:тип (например: 0:int или name:float)")
                print("Поддерживаемые типы: int, float, bool, str, datetime")
                types_input = input("Введите типы через запятую: ").split(',')
                types_dict = {}
                by_number = input("Использовать номера столбцов? (y/n): ").strip().lower() == 'y'

                for type_str in types_input:
                    if ':' in type_str:
                        col, col_type = type_str.split(':', 1)
                        col = int(col) if by_number else col.strip()
                        types_dict[col] = col_type.strip()

                processor.set_column_types(types_dict, by_number)
                print("Типы столбцов установлены")

            elif choice == "7":
                column_input = input("Введите номер или имя столбца: ").strip()
                try:
                    column = int(column_input)
                except ValueError:
                    column = column_input

                values = processor.get_values(column)
                print(f"Значения столбца {column}:")
                for i, value in enumerate(values):
                    print(f"  Строка {i}: {value}")

            elif choice == "8":
                column_input = input("Введите номер или имя столбца: ").strip()
                try:
                    column = int(column_input)
                except ValueError:
                    column = column_input

                value = processor.get_value(column)
                print(f"Первое значение столбца {column}: {value}")

            elif choice == "9":
                column_input = input("Введите номер или имя столбца: ").strip()
                try:
                    column = int(column_input)
                except ValueError:
                    column = column_input

                values_input = input("Введите значения через запятую: ").split(',')
                values = [v.strip() for v in values_input]
                processor.set_values(values, column)
                print("Значения установлены")

            elif choice == "10":
                column_input = input("Введите номер или имя столбца: ").strip()
                try:
                    column = int(column_input)
                except ValueError:
                    column = column_input

                value = input("Введите значение: ").strip()
                processor.set_value(value, column)
                print("Значение установлено")

            elif choice == "11":
                processor.print_table()

            elif choice == "12":  # Арифметические операции
                print("\nАрифметические операции:")
                print("1) Сложение (add)")
                print("2) Вычитание (sub)")
                print("3) Умножение (mul)")
                print("4) Деление (div)")

                op_choice = input("Выберите операцию (1-4): ").strip()

                if op_choice in ["1", "2", "3", "4"]:
                    column1 = input("Введите имя первого столбца: ").strip()
                    column2 = input("Введите имя второго столбца: ").strip()

                    try:
                        if op_choice == "1":
                            processor.add(column1, column2)
                            print(f"Сложение выполнено. Результат в столбце {column1}")
                        elif op_choice == "2":
                            processor.sub(column1, column2)
                            print(f"Вычитание выполнено. Результат в столбце {column1}")
                        elif op_choice == "3":
                            processor.mul(column1, column2)
                            print(f"Умножение выполнено. Результат в столбце {column1}")
                        elif op_choice == "4":
                            processor.div(column1, column2)
                            print(f"Деление выполнено. Результат в столбце {column1}")

                        # Показать результат
                        print("\nРезультат операции:")
                        processor.print_table()

                    except Exception as e:
                        print(f"Ошибка при выполнении операции: {e}")
                else:
                    print("Неверный выбор операции")

            elif choice == "13":  # Операции сравнения
                print("\nОперации сравнения:")
                print("1) Равно (eq)")
                print("2) Больше (gr)")
                print("3) Меньше (ls)")
                print("4) Больше или равно (ge)")
                print("5) Меньше или равно (le)")
                print("6) Не равно (ne)")

                op_choice = input("Выберите операцию (1-6): ").strip()

                if op_choice in ["1", "2", "3", "4", "5", "6"]:
                    column1 = input("Введите имя первого столбца: ").strip()
                    column2 = input("Введите имя второго столбца: ").strip()

                    try:
                        result = []
                        if op_choice == "1":
                            result = processor.eq(column1, column2)
                            print("Результат сравнения 'равно':")
                        elif op_choice == "2":
                            result = processor.gr(column1, column2)
                            print("Результат сравнения 'больше':")
                        elif op_choice == "3":
                            result = processor.ls(column1, column2)
                            print("Результат сравнения 'меньше':")
                        elif op_choice == "4":
                            result = processor.ge(column1, column2)
                            print("Результат сравнения 'больше или равно':")
                        elif op_choice == "5":
                            result = processor.le(column1, column2)
                            print("Результат сравнения 'меньше или равно':")
                        elif op_choice == "6":
                            result = processor.ne(column1, column2)
                            print("Результат сравнения 'не равно':")

                        # Вывести результат
                        for i, val in enumerate(result):
                            print(f"  Строка {i}: {val}")

                        # Предложить фильтрацию
                        filter_choice = input("\nХотите применить фильтрацию по результату? (y/n): ").strip().lower()
                        if filter_choice == 'y':
                            filtered = processor.filter_rows(result)
                            print("\nОтфильтрованная таблица:")
                            filtered.print_table()

                    except Exception as e:
                        print(f"Ошибка при выполнении операции: {e}")
                else:
                    print("Неверный выбор операции")

            elif choice == "14":  # Фильтрация строк
                print("Фильтрация строк по булевому списку")
                print("Введите булевы значения через запятую (True/False):")
                bool_input = input("Пример: True,False,True,True: ").strip()

                try:
                    bool_list = []
                    for item in bool_input.split(','):
                        item = item.strip()
                        if item.lower() == 'true':
                            bool_list.append(True)
                        elif item.lower() == 'false':
                            bool_list.append(False)
                        else:
                            print(f"Неверное значение: {item}. Используйте True или False.")
                            raise ValueError

                    copy_table = input("Копировать таблицу? (y/n): ").strip().lower() == 'y'
                    filtered = processor.filter_rows(bool_list, copy_table)
                    print("\nОтфильтрованная таблица:")
                    filtered.print_table()

                except Exception as e:
                    print(f"Ошибка при фильтрации: {e}")

            elif choice == "15":  # Объединение таблиц (concat)
                print("Объединение двух таблиц (concat)")
                print("1) Объединить с другой загруженной таблицей")
                print("2) Создать две новые таблицы для объединения")

                sub_choice = input("Выберите вариант (1-2): ").strip()

                if sub_choice == "1":
                    if len(loaded_tables) < 2:
                        print("Нужно загрузить как минимум 2 таблицы")
                        continue

                    print(f"Доступно таблиц: {len(loaded_tables)}")
                    for i, table_data in enumerate(loaded_tables):
                        temp_table = Table()
                        temp_table.table = table_data.copy()
                        print(f"{i}: {temp_table}")

                    idx1 = int(input("Введите номер первой таблицы: "))
                    idx2 = int(input("Введите номер второй таблицы: "))

                    if 0 <= idx1 < len(loaded_tables) and 0 <= idx2 < len(loaded_tables):
                        table1 = Table()
                        table1.table = loaded_tables[idx1].copy()
                        table2 = Table()
                        table2.table = loaded_tables[idx2].copy()

                        result = processor.concat(table1, table2)
                        print("Таблицы успешно объединены:")
                        result.print_table()

                        # Сохранить результат как новую таблицу
                        save_choice = input("Сохранить результат как новую таблицу? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            loaded_tables.append(result.table.copy())
                            print("Результат сохранен в список таблиц")
                    else:
                        print("Неверные номера таблиц")

                elif sub_choice == "2":
                    print("Создание первой таблицы для объединения")
                    # Создать простые таблицы для демонстрации
                    table1 = Table()
                    table1.table = {
                        'A': [1, 2, 3],
                        'B': [4, 5, 6]
                    }
                    table1.column_names = ['A', 'B']

                    table2 = Table()
                    table2.table = {
                        'A': [7, 8, 9],
                        'B': [10, 11, 12]
                    }
                    table2.column_names = ['A', 'B']

                    result = processor.concat(table1, table2)
                    print("Таблицы успешно объединены:")
                    result.print_table()
                else:
                    print("Неверный выбор")

            elif choice == "16":  # Разделение таблицы (split)
                print("Разделение текущей таблицы")
                if len(processor) == 0:
                    print("Таблица пуста")
                    continue

                row_number = int(input(f"Введите номер строки для разделения (0-{len(processor) - 1}): "))

                try:
                    table1, table2 = processor.split(row_number)

                    print("\nПервая часть таблицы (до строки {}):".format(row_number))
                    table1.print_table()

                    print("\nВторая часть таблицы (со строки {}):".format(row_number))
                    table2.print_table()

                    # Предложить сохранить части
                    save_choice = input("\nСохранить части как новые таблицы? (y/n): ").strip().lower()
                    if save_choice == 'y':
                        loaded_tables.append(table1.table.copy())
                        loaded_tables.append(table2.table.copy())
                        print("Части сохранены в список таблиц")

                except Exception as e:
                    print(f"Ошибка при разделении: {e}")

            elif choice == "17":  # Слияние таблиц (merge_tables)
                print("Слияние двух таблиц (merge_tables)")
                print("1) Объединить по номерам строк")
                print("2) Объединить по ключевому столбцу")

                sub_choice = input("Выберите тип слияния (1-2): ").strip()

                if sub_choice == "1":
                    by_number = True
                    print("Слияние по номерам строк (таблицы должны иметь одинаковое количество строк)")
                elif sub_choice == "2":
                    by_number = False
                    print("Слияние по ключевому столбцу (первый столбец первой таблицы)")
                else:
                    print("Неверный выбор")
                    continue

                print("\nСоздание таблиц для слияния...")
                # Создать демонстрационные таблицы
                table1 = Table()
                table2 = Table()

                if by_number:
                    # Таблицы для слияния по номерам
                    table1.table = {
                        'ID': [1, 2, 3],
                        'Name': ['Alice', 'Bob', 'Charlie']
                    }
                    table1.column_names = ['ID', 'Name']

                    table2.table = {
                        'ID': [1, 2, 3],
                        'Age': [25, 30, 35],
                        'Salary': [50000, 60000, 70000]
                    }
                    table2.column_names = ['ID', 'Age', 'Salary']
                else:
                    # Таблицы для слияния по ключу
                    table1.table = {
                        'ID': [1, 2, 3, 4],
                        'Name': ['Alice', 'Bob', 'Charlie', 'David']
                    }
                    table1.column_names = ['ID', 'Name']

                    table2.table = {
                        'ID': [2, 3, 4, 5],
                        'Age': [30, 35, 40, 45],
                        'Department': ['IT', 'HR', 'Sales', 'Marketing']
                    }
                    table2.column_names = ['ID', 'Age', 'Department']

                print("Первая таблица:")
                table1.print_table()

                print("\nВторая таблица:")
                table2.print_table()

                try:
                    result = processor.merge_tables(table1, table2, by_number)
                    print("\nРезультат слияния:")
                    result.print_table()
                except Exception as e:
                    print(f"Ошибка при слиянии: {e}")

            elif choice == "18":  # Показать все загруженные таблицы
                print(f"\nВсего загружено таблиц: {len(loaded_tables)}")
                for i, table_data in enumerate(loaded_tables):
                    temp_table = Table()
                    temp_table.table = table_data.copy()
                    print(f"Таблица {i}: {temp_table}")

            elif choice == "19":  # Выбрать активную таблицу
                if not loaded_tables:
                    print("Нет загруженных таблиц")
                    continue

                print(f"Доступно таблиц: {len(loaded_tables)}")
                for i, table_data in enumerate(loaded_tables):
                    temp_table = Table()
                    temp_table.table = table_data.copy()
                    print(f"{i}: {temp_table}")

                try:
                    idx = int(input("Введите номер таблицы для активации: "))
                    if 0 <= idx < len(loaded_tables):
                        processor.table = loaded_tables[idx].copy()
                        processor.column_names = list(processor.table.keys())
                        processor._auto_detect_column_types()
                        print(f"Таблица {idx} активирована")
                    else:
                        print("Неверный номер таблицы")
                except ValueError:
                    print("Введите корректный номер")

            elif choice == "20":  # Создать новую таблицу
                print("Создание новой таблицы")
                num_cols = int(input("Введите количество столбцов: "))
                num_rows = int(input("Введите количество строк: "))

                new_table = {}
                for col in range(num_cols):
                    col_name = input(f"Введите имя для столбца {col}: ")
                    values = []
                    for row in range(num_rows):
                        value = input(f"  Строка {row}, столбец {col_name}: ")
                        values.append(value)
                    new_table[col_name] = values

                processor.table = new_table
                processor.column_names = list(new_table.keys())
                processor._auto_detect_column_types()
                loaded_tables.append(new_table.copy())
                print("Новая таблица создана и активирована")

            elif choice == "21":  # Удалить таблицу
                if not loaded_tables:
                    print("Нет загруженных таблиц")
                    continue

                print(f"Доступно таблиц: {len(loaded_tables)}")
                for i, table_data in enumerate(loaded_tables):
                    temp_table = Table()
                    temp_table.table = table_data.copy()
                    print(f"{i}: {temp_table}")

                try:
                    idx = int(input("Введите номер таблицы для удаления: "))
                    if 0 <= idx < len(loaded_tables):
                        if loaded_tables[idx] == processor.table:
                            print("Нельзя удалить активную таблицу. Сначала выберите другую.")
                        else:
                            del loaded_tables[idx]
                            print(f"Таблица {idx} удалена")
                    else:
                        print("Неверный номер таблицы")
                except ValueError:
                    print("Введите корректный номер")

            elif choice == "22":  # Проверить состояние текущей таблицы
                print(f"Текущая таблица: {processor}")
                print(f"Количество столбцов: {len(processor.column_names)}")
                print(f"Количество строк: {len(processor)}")
                print("Столбцы:", ", ".join(processor.column_names))

                if processor.table:
                    print("\nПервые 3 строки таблицы:")
                    if len(processor) > 0:
                        sample = processor.get_rows_by_number(0, min(2, len(processor) - 1))
                        sample.print_table()

            else:
                print("Неверный выбор. Попробуйте снова.")

        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()