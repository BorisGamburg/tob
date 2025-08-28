import sys
import logging
from config_manager import ConfigManager

class DummyInstance:
    """Фиктивный класс для тестирования ConfigManager."""
    def __init__(self):
        pass

def setup_logging():
    """Настраивает логирование."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Основная функция для обновления параметра в конфигурационном файле."""
    config_file_path = sys.argv[1]
    param = sys.argv[2]
    value = sys.argv[3]
    type = sys.argv[4]

    # Настраиваем логирование
    logger = setup_logging()

    try:
        # Создаем фиктивный экземпляр для ConfigManager
        instance = DummyInstance()
        
        # Инициализируем ConfigManager
        config_manager = ConfigManager(config_file_path, instance, logger)

        # Устанавливаем параметр
        config_manager.set_config_param(param, value, type)
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении конфигурации: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()