import logging
import ast # Добавляем импорт модуля ast для безопасного парсинга строк

class Stack:
    def __init__(self):
        """Инициализация пустого стека."""
        self.items = []
        self.logger = logging.getLogger(__name__)
        # Настройка логгера для тестового примера, если еще не настроен
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

    def is_empty(self):
        """Проверка, пуст ли стек."""
        return len(self.items) == 0

    def push(self, item):
        """Добавление элемента в стек (в конец списка)."""
        self.items.append(item)
        self.logger.info(f"Элемент добавлен в стек: {item}. Текущий размер стека: {self.size()}")

    def pop(self):
        """Удаление и возврат последнего элемента из стека."""
        if self.is_empty():
            self.logger.warning("Попытка извлечь элемент из пустого стека.")
            return None
        item = self.items.pop()
        self.logger.debug(f"Элемент извлечен из стека: {item}. Текущий размер стека: {self.size()}")
        return item

    def peek(self):
        """Просмотр последнего элемента без удаления."""
        if self.is_empty():
            #self.logger.info("Попытка просмотреть пустой стек.")
            return None
        return self.items[-1]
    
    def peek_second_last(self):
        """Просмотр предпоследнего элемента без удаления."""
        if len(self.items) < 2:
            self.logger.debug("Попытка просмотреть предпоследний элемент в стеке с менее чем двумя элементами.")
            return None
        return self.items[-2]    

    def size(self):
        """Возврат размера стека."""
        return len(self.items)

    def from_string(self, string):
        """
        Устанавливает стек из строки, используя ast.literal_eval для безопасного
        преобразования строкового представления списка обратно в объекты Python.
        Это позволяет корректно парсить кортежи и другие типы данных.
        """
        try:
            # Безопасно оцениваем строку как литерал Python (ожидается список)
            parsed_list = ast.literal_eval(string)
            if not isinstance(parsed_list, list):
                raise ValueError("Строка должна представлять собой список Python (например, '[(1, 2), (3, 4)]').")
            self.items = parsed_list
            self.logger.info(f"Стек установлен из строки: '{string}'.")
        except (ValueError, SyntaxError) as e:
            self.logger.error(f"Ошибка при парсинге строки '{string}' в from_string: {e}")
            raise ValueError(f"Невозможно распарсить строку как список: {string}") from e

    def to_string(self):
        """
        Возвращает стек в виде строкового представления списка Python.
        Это позволяет корректно сериализовать кортежи и другие типы данных.
        """
        return str(self.items) # Возвращает строку вида '[(10.0, 1), (20.0, 2)]'


# --- Тестовый пример для работы с кортежами ---
if __name__ == "__main__":
    print("Запуск тестов класса Stack с кортежами...")

    # Создаем экземпляр стека
    my_stack = Stack()
    print(f"Стек пуст в начале? {my_stack.is_empty()}") # Ожидается: True

    # Тест 1: Добавление кортежей в стек
    print("\n--- Тест 1: Добавление элементов ---")
    price1, qty1 = 150.75, 10
    price2, qty2 = 151.20, 5
    price3, qty3 = 149.90, 12

    my_stack.push((price1, qty1))
    my_stack.push((price2, qty2))
    my_stack.push((price3, qty3))

    print(f"Размер стека после добавления 3 элементов: {my_stack.size()}") # Ожидается: 3
    assert my_stack.size() == 3, "Тест 1 провален: Неверный размер стека после push."
    print("Тест 1 пройден: Элементы успешно добавлены.")

    # Тест 2: Просмотр верхнего элемента (peek)
    print("\n--- Тест 2: Просмотр верхнего элемента ---")
    top_item = my_stack.peek()
    print(f"Верхний элемент стека: {top_item}") # Ожидается: (149.9, 12)
    assert top_item == (price3, qty3), "Тест 2 провален: peek вернул неверный элемент."
    print(f"Размер стека после peek: {my_stack.size()}") # Ожидается: 3 (размер не меняется)
    assert my_stack.size() == 3, "Тест 2 провален: Размер стека изменился после peek."
    print("Тест 2 пройден: peek работает корректно.")

    # Тест 2.1: Просмотр предпоследнего элемента (peek_second_last)
    print("\n--- Тест 2.1: Просмотр предпоследнего элемента ---")
    top_item = my_stack.peek_second_last()
    print(f"Верхний элемент стека: {top_item}") 
    assert top_item == (price2, qty2), "Тест 2.1 провален: peek вернул неверный элемент."
    print(f"Размер стека после peek_second_last: {my_stack.size()}") # Ожидается: 3 (размер не меняется)
    assert my_stack.size() == 3, "Тест 2.1 провален: Размер стека изменился после peek."
    print("Тест 2.1 пройден: peek_second_last работает корректно.")

    # Тест 3: Извлечение элементов (pop)
    print("\n--- Тест 3: Извлечение элементов ---")
    popped_item1 = my_stack.pop()
    print(f"Извлеченный элемент: {popped_item1}") # Ожидается: (149.9, 12)
    assert popped_item1 == (price3, qty3), "Тест 3 провален: pop вернул неверный первый элемент."
    print(f"Размер стека после первого pop: {my_stack.size()}") # Ожидается: 2

    popped_item2 = my_stack.pop()
    print(f"Извлеченный элемент: {popped_item2}") # Ожидается: (151.2, 5)
    assert popped_item2 == (price2, qty2), "Тест 3 провален: pop вернул неверный второй элемент."
    print(f"Размер стека после второго pop: {my_stack.size()}") # Ожидается: 1

    popped_item3 = my_stack.pop()
    print(f"Извлеченный элемент: {popped_item3}") # Ожидается: (150.75, 10)
    assert popped_item3 == (price1, qty1), "Тест 3 провален: pop вернул неверный третий элемент."
    print(f"Размер стека после третьего pop: {my_stack.size()}") # Ожидается: 0

    assert my_stack.is_empty(), "Тест 3 провален: Стек не пуст после извлечения всех элементов."
    print("Тест 3 пройден: Элементы успешно извлечены, стек пуст.")

    # Тест 4: Извлечение из пустого стека
    print("\n--- Тест 4: Извлечение из пустого стека ---")
    popped_from_empty = my_stack.pop()
    print(f"Попытка извлечь из пустого стека: {popped_from_empty}") # Ожидается: None
    assert popped_from_empty is None, "Тест 4 провален: pop из пустого стека должен вернуть None."
    print("Тест 4 пройден: pop из пустого стека работает корректно.")

    # Тест 5: from_string и to_string (с учетом обработки кортежей)
    print("\n--- Тест 5: from_string и to_string ---")
    # Очищаем стек для нового теста
    my_stack = Stack() 
    my_stack.push((10.0, 1))
    my_stack.push((20.0, 2))
    
    stack_as_string = my_stack.to_string()
    print(f"Стек в виде строки: '{stack_as_string}'") # Ожидается: '[(10.0, 1), (20.0, 2)]'

    new_stack = Stack()
    new_stack.from_string(stack_as_string)
    print(f"Новый стек после from_string: {new_stack.items}")
    # Проверка, что элементы являются кортежами, а не строками
    assert new_stack.items == [(10.0, 1), (20.0, 2)], "Тест 5 провален: from_string/to_string неверно обработали кортежи."
    print("Тест 5 пройден: from_string и to_string корректно обрабатывают кортежи.")

    print("\nВсе тесты завершены.")
