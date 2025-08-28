import requests
from config_manager import ConfigManager

class Telegram:
    def __init__(self, logger):
        self.logger = logger
        self.telegram_token = ""
        self.telegram_chat_id = ""

        # Инициализация конфигa
        self.config_manager = ConfigManager(config_file='telegram_config.txt', instance=self, logger=logger)  
        self.config_manager.load_config_to_instance()
        
    def send_telegram_message(self, message):
        """Отправляет сообщение в Telegram."""
        if not self.telegram_token or not self.telegram_chat_id:
            self.logger.warning("Telegram token или chat_id не указаны в config.txt, уведомления не отправлены.")
            return
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        params = {
            "chat_id": self.telegram_chat_id,
            "text": message
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code != 200:
                self.logger.error(f"Не удалось отправить сообщение в Telegram: {response.text}")
        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")

