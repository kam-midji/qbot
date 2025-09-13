# q_bot/trade_manager.py

"""
The core trading logic engine for Q.bot.

This module contains the primary functions that govern the bot's behavior,
including checking for trading signals, managing position sizes, calculating
risk parameters (Stop Loss and Take Profit), supervising manual trades, and
handling the end-of-day closure process.
"""

import logging
import math
from datetime import datetime
import MetaTrader5 as mt5

from . import config
from . import mt5_connector
from . import signal_generator

log = logging.getLogger(__name__)

# --- Private Helper Functions ---

def _calculate_lot_size(probability, balance):
    """
    Calculates the trade volume based on signal probability and account balance.
    """
    lot_per_10k = 0
    # The keys in POSITION_SIZING_MAP should be sorted descending to find the correct tier
    for threshold in sorted(config.POSITION_SIZING_MAP.keys(), reverse=True):
        if probability > threshold:
            lot_per_10k = config.POSITION_SIZING_MAP[threshold]
            break

    if lot_per_10k == 0:
        return 0.0

    # Calculate lot size and normalize it to a valid value for the broker
    lot_size = (balance / config.LOT_SIZE_PER_BALANCE) * lot_per_10k
    symbol_info = mt5_connector.get_symbol_info(config.ASSET)
    if not symbol_info:
        log.error("Could not get symbol info to validate lot size.")
        return 0.0

    # Ensure lot size is not smaller than the minimum allowed
    if lot_size < symbol_info.volume_min:
        log.warning(f"Calculated lot size {lot_size} is less than minimum {symbol_info.volume_min}. Clamping to minimum.")
        return symbol_info.volume_min

    # Adjust lot size to be a multiple of the volume step
    step = symbol_info.volume_step
    lot_size = math.floor(lot_size / step) * step

    return round(lot_size, 2)


def _calculate_tp_sl(direction, entry_price, lot_size):
    """
    Calculates the Take Profit and Stop Loss prices for a new trade.
    """
    symbol_info = mt5_connector.get_symbol_info(config.ASSET)
    if not symbol_info:
        log.error("Could not get symbol info to calculate TP/SL.")
        return None, None

    point = symbol_info.point

    # --- Take Profit Calculation ---
    tp_distance = config.TAKE_PROFIT_PIPS * 10 * point # 1 pip = 10 points for 5-digit brokers
    if direction == "UP":
        take_profit = entry_price + tp_distance
    else: # DOWN
        take_profit = entry_price - tp_distance

    # --- Stop Loss Calculation ---
    account_info = mt5_connector.get_account_info()
    loss_in_currency = account_info.balance * (config.STOP_LOSS_BALANCE_PERCENT / 100)

    # trade_tick_value is the value of a one-tick move in the deposit currency
    tick_value = symbol_info.trade_tick_value
    if tick_value <= 0:
        log.error(f"Symbol {config.ASSET} has an invalid tick value: {tick_value}. Cannot calculate SL.")
        return None, None

    # Calculate how many points of movement equals the desired currency loss
    loss_in_points = (loss_in_currency / (lot_size * tick_value)) * point

    if direction == "UP":
        stop_loss = entry_price - loss_in_points
    else: # DOWN
        stop_loss = entry_price + loss_in_points

    return round(take_profit, symbol_info.digits), round(stop_loss, symbol_info.digits)


def _open_new_position(direction, probability):
    """
    Orchestrates the process of opening a new trade.
    """
    log.info(f"Attempting to open new position for signal: {direction} @ {probability:.2f}%")

    account_info = mt5_connector.get_account_info()
    lot_size = _calculate_lot_size(probability, account_info.balance)
    if lot_size == 0.0:
        log.warning("Calculated lot size is 0.0, aborting trade.")
        return

    order_type = mt5.ORDER_TYPE_BUY if direction == "UP" else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(config.ASSET).ask if direction == "UP" else mt5.symbol_info_tick(config.ASSET).bid

    take_profit, stop_loss = _calculate_tp_sl(direction, price, lot_size)
    if take_profit is None or stop_loss is None:
        log.error("Failed to calculate TP/SL, aborting trade.")
        return

    comment = f"Q.bot Signal {probability:.1f}%"
    mt5_connector.place_order(config.ASSET, order_type, lot_size, stop_loss, take_profit, comment)


# --- Public Functions ---

def handle_end_of_day_closure():
    """
    Checks if it's the end-of-day close time and closes all open trades.
    """
    server_time = datetime.fromtimestamp(mt5.terminal_info().time)
    close_time_str = server_time.strftime('%Y-%m-%d') + " " + config.END_OF_DAY_CLOSE_TIME
    close_time = datetime.strptime(close_time_str, '%Y-%m-%d %H:%M')

    if server_time >= close_time:
        log.info(f"End-of-day closure time ({config.END_OF_DAY_CLOSE_TIME}) reached. Closing all trades.")
        open_positions = mt5_connector.get_open_positions(symbol=config.ASSET)
        if not open_positions:
            log.info("No open positions to close.")
            return

        for position in open_positions:
            log.info(f"Closing position #{position.ticket} due to EOD.")
            mt5_connector.close_position(position, comment="EOD Closure")


def manage_manual_trades():
    """
    Monitors for manually opened trades and applies standard TP/SL.
    """
    open_positions = mt5_connector.get_open_positions(symbol=config.ASSET)
    if not open_positions:
        return

    for position in open_positions:
        # A manual trade is identified by a magic number of 0
        if position.magic == 0 and position.tp == 0.0 and position.sl == 0.0:
            log.info(f"Found unmanaged manual trade #{position.ticket}. Applying standard TP/SL.")
            direction = "UP" if position.type == mt5.ORDER_TYPE_BUY else "DOWN"

            take_profit, stop_loss = _calculate_tp_sl(direction, position.price_open, position.volume)
            if take_profit and stop_loss:
                mt5_connector.modify_position(position.ticket, stop_loss, take_profit)


def check_for_new_trades():
    """
    Checks for new signals and opens a trade if entry conditions are met.
    """
    open_positions = mt5_connector.get_open_positions(symbol=config.ASSET)
    bot_positions = [p for p in open_positions if p.magic == config.MAGIC_NUMBER] if open_positions else []

    if len(bot_positions) >= config.MAX_CONCURRENT_TRADES:
        log.debug(f"Max concurrent trades ({config.MAX_CONCURRENT_TRADES}) reached. No new trades will be opened.")
        return

    direction, probability = signal_generator.get_trading_signal()
    if direction and probability:
        _open_new_position(direction, probability)


def run_trade_cycle():
    """
    Executes one full cycle of the bot's trading logic.
    """
    log.debug("--- Starting new trade cycle ---")

    # 1. Handle EOD closure first, as it's a hard stop
    handle_end_of_day_closure()

    # 2. Supervise any manual trades
    manage_manual_trades()

    # 3. Check for opportunities to open new trades
    check_for_new_trades()

    log.debug("--- Trade cycle finished ---")
