# Purpose: Logs application events (e.g., errors, requests).
# Features:
# Logs to console with different log levels.
# Supports levels like info, warn, error, and debug.

import logging

class Logger:
    def __init__(self):
        # Configure the logger
        logging.basicConfig(
            format="[%(levelname)s]: %(message)s",
            level=logging.DEBUG  # Set default log level
        )
        self.logger = logging.getLogger("custom_logger")

    def info(self, message):
        self.logger.info(message)

    def warn(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def debug(self, message):
        self.logger.debug(message)

# Create a single instance of the logger
logger = Logger()

# Export the logger instance for use in other files
