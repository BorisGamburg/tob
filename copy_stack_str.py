from config_manager import ConfigManager
import logging
import argparse


parser = argparse.ArgumentParser(description="My program")
parser.add_argument('source_config', type=str, help='Path to a file')
parser.add_argument('target_config', type=str, help='Number of iterations to run')
args = parser.parse_args()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - PID:%(process)d - %(message)s')
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)


# Читаем что копировать
config_manager = ConfigManager(
    config_file=args.source_config, 
    instance=None, 
    logger=logger
)
order_stack_str_source = config_manager.read_config_param("order_stack_str")
# print(order_stack_str_source)

# Копируем
config_manager.config_file = args.target_config
config_manager.set_config_param("order_stack_str", order_stack_str_source, "string")
order_stack_str = config_manager.read_config_param("order_stack_str")
#print(order_stack_str)

