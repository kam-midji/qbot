# q_bot/config.py

"""
Configuration file for Q.bot.

This file holds all the core parameters for the bot's operation,
from MetaTrader 5 connection details to the trading strategy rules.
Please fill in your account details before running the bot.
"""

# -- MetaTrader 5 Configuration --
# These details are required to connect to your trading account.
# PLEASE FILL IN YOUR CREDENTIALS AND TERMINAL PATH.
MT5_LOGIN = 12345678  # Your account number
MT5_PASSWORD = "YOUR_PASSWORD"  # Your password
MT5_SERVER = "YOUR_SERVER"  # Your broker's server name
# Example for Windows: r"C:\Program Files\MetaTrader 5\terminal64.exe"
MT5_TERMINAL_PATH = r"path/to/your/terminal64.exe"


# -- Trading Strategy Parameters --
ASSET = "EURUSD"


# -- Risk Management --
MAX_CONCURRENT_TRADES = 3
TAKE_PROFIT_PIPS = 2.0  # Take profit in pips
# Stop loss as a percentage of the total account balance
STOP_LOSS_BALANCE_PERCENT = 0.1


# -- Position Sizing --
# Defines the lot size per a certain amount of account balance, based on signal probability.
# A dictionary where keys are the minimum probability threshold (e.g., 85 for >85%)
# and values are the lots per the balance unit defined below.
POSITION_SIZING_MAP = {
    85: 0.01,  # For signals with >85% probability
    90: 0.01,  # For signals with >90% probability
    95: 0.02,  # For signals with >95% probability
}
# The balance unit for lot size calculation (e.g., per $10,000)
LOT_SIZE_PER_BALANCE = 10000


# -- Sharia-Compliant End-of-Day Closure --
# To avoid swap fees, all trades will be closed at this time.
# Time is in the broker's server time (24-hour format).
# Example: "23:50" means 11:50 PM server time.
END_OF_DAY_CLOSE_TIME = "23:50"


# -- Signal Generation (for Placeholder) --
# While the real models are external, these parameters can influence the placeholder.
# The list of timeframes the LSTM models analyze.
# The user specified 12 models; these are the most common ones.
ANALYST_TIMEFRAMES = [
    "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"
]
# Weights for votes from different timeframes (used by placeholder)
TIMEFRAME_WEIGHTS = {
    "high": ["H4", "D1"],
    "medium": ["M30", "H1"],
    "low": ["M1", "M5", "M15"] # M15 added here as an example
}


# -- Bot Operation --
MAGIC_NUMBER = 202407  # A unique number to identify trades opened by this bot.

# Order execution filling mode. Can be "FOK", "IOC", or "RETURN".
# FOK (Fill Or Kill): The order must be executed in the specified volume, otherwise it's canceled.
# IOC (Immediate Or Cancel): The trader agrees to execute a deal with the maximum available volume in the market within that indicated in the order. The remaining volume is canceled.
# Most brokers support FOK. Change if you get "Unsupported filling mode" errors.
FILLING_MODE = "FOK"

# Time to wait in seconds between each main loop iteration
LOOP_SLEEP_SECONDS = 5
# The timeframe the bot primarily operates on for signals
# and the prediction target for the ML models in minutes.
PRIMARY_TIMEFRAME = "M15"
PREDICTION_TARGET_MINUTES = 15
LOG_FILE = "q_bot_activity.log"
LOG_LEVEL = "INFO" # e.g., "DEBUG", "INFO", "WARNING", "ERROR"
