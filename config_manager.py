import os
import logging

class ConfigManager:
    """Управляет загрузкой и обновлением конфигурационных данных для стратегии."""
    def __init__(self, config_file, instance, logger):
        """Инициализирует менеджер конфигурации."""
        self.config_file = config_file
        self.instance = instance
        self.logger = logger

    def set_instance_attr(self, param, value):
        if param is None:
            return
        
        if hasattr(self.instance, param):
            setattr(self.instance, param, value)
        else:
            raise Exception(f"{param}: неправильное название параметра в конфигфайле")

    def _get_param_value(self, value):
        """Возвращает значение параметра с определением его типа."""
        value = value.strip()

        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]

        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        
        if value.lower() == 'none':
            return None

        if '%' in value:
            try:
                percent_str = value[:value.index('%')]
                percent_value = float(percent_str) / 100
                return (percent_value, "percent")
            except (ValueError, IndexError):
                pass

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        raise ValueError(f"Невозможно определить тип значения '{value}'")

    def _parse_config_line(self, line):
        """Парсит строку конфига и устанавливает параметры в instance."""
        line = line.strip()
        if not line or line.startswith('#'):
            return None, None
        if '=' not in line:
            raise ValueError(f"Строка '{line}' в файле конфигурации не содержит '='. Ожидается формат 'параметр = значение'.")
        param, value = line.split('=', 1)
        param, value = param.strip(), value.strip()
        parsed_value = self._get_param_value(value)
        return param, parsed_value

    def load_config_to_instance(self):
        """Читает и парсит конфигурационный файл."""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            for line in f:
                param, value = self._parse_config_line(line)
                self.set_instance_attr(param, value)


    def set_config_param(self, param, value, type):
        """Устанавливает значение параметра в конфигурационном файле."""
        try:
            lines = []
            param_found = False
            with open(self.config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                p, _ = self._parse_config_line(line)
                if p == param:
                    if type == "string":
                        lines[i] = f"{param}=\"{value}\"\n"
                    elif type == "number":
                        lines[i] = f"{param}={value}\n"
                    elif type == "boolean":
                        lines[i] = f"{param}={str(value).lower()}\n"
                    elif type == "percent":
                        lines[i] = f"{param}={value*100}%\n"
                    elif type == "none":
                        lines[i] = f"{param}=none\n"
                    param_found = True
                    break

            if not param_found:
                self.logger.error(f"Параметр {param} не найден")
                raise ValueError(f"Параметр {param} не найден в конфигурационном файле")

            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            self.logger.info(f"Параметр {param} успешно установлен в значение {value}")
            
        except FileNotFoundError:
            self.logger.error(f"Файл {self.config_file} не найден при попытке обновления параметра {param}")
            raise
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении параметра {param} в файле {self.config_file}: {e}")
            raise


    def read_config_param(self, param_name):
        """Читает значение указанного параметра из конфигурационного файла."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    p, value = line.split('=', 1)
                    p = p.strip()
                    if p == param_name:
                        return self._get_param_value(value)
            self.logger.error(f"Параметр {param_name} не найден в файле {self.config_file}")
            raise ValueError(f"Параметр {param_name} не найден в конфигурационном файле")
        except FileNotFoundError:
            self.logger.error(f"Файл {self.config_file} не найден при попытке чтения параметра {param_name}")
            raise
        except Exception as e:
            self.logger.error(f"Ошибка при чтении параметра {param_name} из файла {self.config_file}: {e}")
            raise

# Тестовый пример
if __name__ == "__main__":
    print("Запуск тестов ConfigManager...")

    # Создаем временный конфигурационный файл с использованием абсолютного пути
    config_file = os.path.join(os.getcwd(), "test_config.txt")
    print(f"Попытка создать файл: {config_file}")
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("""
# Тестовый конфиг
name="TestBot"
enabled=true
threshold=0.75
percentage=2%
count=42
none_value=none
""")
        if os.path.exists(config_file):
            print(f"Файл {config_file} успешно создан")
        else:
            print(f"Ошибка: Файл {config_file} не был создан")
    except Exception as e:
        print(f"Ошибка при создании файла {config_file}: {e}")
        exit(1)

    # Создаем имитацию объекта instance
    class MockInstance:
        def __init__(self):
            self.name = None
            self.enabled = None
            self.threshold = None
            self.percentage = None
            self.count = None
            self.none_value = None

    instance = MockInstance()

    # Настраиваем простой логгер
    logger = logging.getLogger('test_logger')
    logging.basicConfig(level=logging.INFO)

    # Создаем экземпляр ConfigManager
    config_manager = ConfigManager(config_file, instance, logger)

    # Тест 1: Загрузка конфигурации
    print("\nТест 1: Загрузка конфигурации")
    try:
        config_manager.load_config_to_instance()
        assert instance.name == "TestBot", f"Ожидалось name='TestBot', получено {instance.name}"
        assert instance.enabled is True, f"Ожидалось enabled=True, получено {instance.enabled}"
        assert instance.threshold == 0.75, f"Ожидалось threshold=0.75, получено {instance.threshold}"
        assert instance.percentage == (0.02, "percent"), f"Ожидалось percentage=(0.02, 'percent'), получено {instance.percentage}"
        assert instance.count == 42, f"Ожидалось count=42, получено {instance.count}"
        assert instance.none_value is None, f"Ожидалось none_value=None, получено {instance.none_value}"
        print("Тест 1 пройден: Конфигурация успешно загружена")
    except Exception as e:
        print(f"Тест 1 провален: {e}")

    # Тест 2: Чтение параметров
    print("\nТест 2: Чтение параметров")
    try:
        assert config_manager.read_config_param('name') == "TestBot", "Ошибка при чтении параметра name"
        assert config_manager.read_config_param('enabled') is True, "Ошибка при чтении параметра enabled"
        assert config_manager.read_config_param('threshold') == 0.75, "Ошибка при чтении параметра threshold"
        assert config_manager.read_config_param('percentage') == (0.02, "percent"), "Ошибка при чтении параметра percentage"
        assert config_manager.read_config_param('count') == 42, "Ошибка при чтении параметра count"
        assert config_manager.read_config_param('none_value') is None, "Ошибка при чтении параметра none_value"
        print("Тест 2 пройден: Параметры успешно прочитаны")
    except Exception as e:
        print(f"Тест 2 провален: {e}")

    # Тест 3: Установка параметров
    print("\nТест 3: Установка параметров")
    try:
        config_manager.set_config_param('name', "NewBot", "string")
        assert config_manager.read_config_param('name') == "NewBot", "Ошибка при установке параметра name"
        config_manager.set_config_param('count', 100, "number")
        assert config_manager.read_config_param('count') == 100, "Ошибка при установке параметра count"
        print("Тест 3 пройден: Параметры успешно установлены")
    except Exception as e:
        print(f"Тест 3 провален: {e}")

    # Тест 4: Проверка несуществующего параметра
    print("\nТест 4: Проверка несуществующего параметра")
    try:
        config_manager.read_config_param('non_existent')
        print("Тест 4 провален: Ожидалось исключение для несуществующего параметра")
    except ValueError as e:
        print("Тест 4 пройден: Ожидаемое исключение для несуществующего параметра")

    # Тест 5: Проверка некорректного формата конфигурации
    print("\nТест 5: Проверка некорректного формата конфигурации")
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("invalid_line\n")
        if os.path.exists(config_file):
            print(f"Файл {config_file} успешно перезаписан для теста 5")
        config_manager.load_config_to_instance()
        print("Тест 5 провален: Ожидалось исключение для некорректного формата")
    except ValueError:
        print("Тест 5 пройден: Ожидаемое исключение для некорректного формата")
    except Exception as e:
        print(f"Тест 5 провален: Неожиданная ошибка: {e}")

    print("\nТесты завершены")