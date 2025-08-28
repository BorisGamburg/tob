def _set_config_value(self, param, value, config):
    """Устанавливает значение параметра в словаре с заданным алгоритмом определения типа."""
    value = value.strip()  # Убираем пробельные символы

    # 1. Проверяем, в кавычках ли значение
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        config[param] = value[1:-1]  # Убираем кавычки и сохраняем как строку
        return

    # 2. Пробуем преобразовать в int
    try:
        config[param] = int(value)
        return
    except ValueError:
        pass  # Не удалось преобразовать в int, идём дальше

    # 3. Пробуем преобразовать в float
    try:
        config[param] = float(value)
        return
    except ValueError:
        pass  # Не удалось преобразовать в float, идём дальше

    # 4. Если ни один из вариантов не сработал, выбрасываем исключение
    raise ValueError(f"Невозможно определить тип значения '{value}' для параметра '{param}'")

# Тест
config = {}
class Dummy:
    def _set_config_value(self, param, value, config):
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            config[param] = value[1:-1]
            return
        try:
            config[param] = int(value)
            return
        except ValueError:
            pass
        try:
            config[param] = float(value)
            return
        except ValueError:
            pass
        raise ValueError(f"Невозможно определить тип значения '{value}' для параметра '{param}'")

d = Dummy()
d._set_config_value("symbol", '"BTCUSDT"', config)
d._set_config_value("count", "10", config)
d._set_config_value("step", "0.5", config)
d._set_config_value("neg", "-123", config)
d._set_config_value("exp", "1e-5", config)

print(" ")
print(config)

# Проверка исключения
try:
    d._set_config_value("invalid", "BTCUSDT", config)
except ValueError as e:
    print(e)