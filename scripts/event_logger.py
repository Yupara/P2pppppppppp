import logging

# Настройка логирования
logging.basicConfig(
    filename="events.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_event(event_type, message):
    if event_type == "info":
        logging.info(message)
    elif event_type == "warning":
        logging.warning(message)
    elif event_type == "error":
        logging.error(message)
    else:
        logging.info(f"UNKNOWN EVENT TYPE: {message}")

# Пример использования
if __name__ == "__main__":
    log_event("info", "User logged in successfully.")
    log_event("error", "Failed to create trade due to insufficient balance.")
