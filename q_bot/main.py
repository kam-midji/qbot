# q_bot/main.py

"""
The main entry point for the Q.bot trading application.

This script initializes the connection to MetaTrader 5, sets up logging,
and runs the main trading loop. The loop continuously calls the trade
management cycle, where all the core logic resides.
"""

import logging
import time
import sys

from . import config
from . import mt5_connector
from . import trade_manager

def setup_logging():
    """Configures the logging for the application."""
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Configure root logger
    logger = logging.getLogger('q_bot') # Get logger for the package
    try:
        log_level = getattr(logging, config.LOG_LEVEL.upper())
    except AttributeError:
        log_level = logging.INFO # Default to INFO if config is invalid
        print(f"Invalid LOG_LEVEL '{config.LOG_LEVEL}'. Defaulting to 'INFO'.")
    logger.setLevel(log_level)

    # Prevent logs from propagating to the root logger if it has handlers
    logger.propagate = False

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console Handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_format)
    logger.addHandler(stdout_handler)

    # File Handler
    if config.LOG_FILE:
        try:
            file_handler = logging.FileHandler(config.LOG_FILE)
            file_handler.setFormatter(log_format)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error setting up file logger: {e}")


def main():
    """
    The main function that runs the bot.
    """
    setup_logging()
    log = logging.getLogger(__name__)
    log.info("Starting Q.bot...")

    try:
        # Initialize connection to MetaTrader 5
        if not mt5_connector.initialize():
            log.critical("Failed to initialize MT5 connection. Bot will not start.")
            return # Exit if connection fails

        log.info("Bot is running. Press Ctrl+C to stop.")

        # Main bot loop
        while True:
            trade_manager.run_trade_cycle()
            log.debug(f"Cycle finished. Sleeping for {config.LOOP_SLEEP_SECONDS} seconds.")
            time.sleep(config.LOOP_SLEEP_SECONDS)

    except KeyboardInterrupt:
        log.info("Bot stopped by user (Ctrl+C).")
    except Exception as e:
        log.critical(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        # Ensure the connection is always closed
        log.info("Shutting down MT5 connection.")
        mt5_connector.shutdown()
        log.info("Q.bot has been shut down.")


if __name__ == "__main__":
    main()
