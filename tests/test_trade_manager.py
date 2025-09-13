# tests/test_trade_manager.py

import sys
import unittest
from unittest.mock import patch, MagicMock

# --- Mock the MetaTrader5 module before it's imported by other modules ---
# This is crucial for running tests in an environment where MT5 is not installed.
sys.modules['MetaTrader5'] = MagicMock()

# Now we can import the modules that depend on MetaTrader5
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from q_bot import trade_manager
from q_bot import config

class TestTradeManagerCalculations(unittest.TestCase):

    def setUp(self):
        """Set up mock objects for testing."""
        # Mock for symbol_info
        self.mock_symbol_info = MagicMock()
        self.mock_symbol_info.point = 0.00001
        self.mock_symbol_info.digits = 5
        self.mock_symbol_info.volume_min = 0.01
        self.mock_symbol_info.volume_step = 0.01
        self.mock_symbol_info.trade_tick_value = 1.0  # Assuming 1 USD per tick for simplicity

        # Mock for account_info
        self.mock_account_info = MagicMock()
        self.mock_account_info.balance = 20000.0

    @patch('q_bot.trade_manager.mt5_connector')
    def test_calculate_lot_size(self, mock_mt5_connector):
        """
        Tests the _calculate_lot_size function with various probabilities.
        """
        mock_mt5_connector.get_symbol_info.return_value = self.mock_symbol_info

        # Test case 1: >95% probability tier
        # Balance is $20,000, so 2 * 0.02 = 0.04 lots
        lot_size = trade_manager._calculate_lot_size(96.0, 20000)
        self.assertEqual(lot_size, 0.04)

        # Test case 2: >90% probability tier
        # Balance is $20,000, so 2 * 0.01 = 0.02 lots
        lot_size = trade_manager._calculate_lot_size(92.0, 20000)
        self.assertEqual(lot_size, 0.02)

        # Test case 3: >85% probability tier
        # Balance is $20,000, so 2 * 0.01 = 0.02 lots
        lot_size = trade_manager._calculate_lot_size(88.0, 20000)
        self.assertEqual(lot_size, 0.02)

        # Test case 4: Below threshold
        lot_size = trade_manager._calculate_lot_size(80.0, 20000)
        self.assertEqual(lot_size, 0.0)

        # Test case 5: Lot size clamping to volume_min
        # Balance is $100, calc would be (100/10000)*0.01 = 0.0001, which is < 0.01
        lot_size = trade_manager._calculate_lot_size(88.0, 100)
        self.assertEqual(lot_size, 0.01)

        # Test case 6: Lot size step adjustment
        # Balance $28,000 -> (28000/10000)*0.02 = 0.056. Should be rounded down to 0.05
        lot_size = trade_manager._calculate_lot_size(96.0, 28000)
        self.assertEqual(lot_size, 0.05)


    @patch('q_bot.trade_manager.mt5_connector')
    def test_calculate_tp_sl(self, mock_mt5_connector):
        """
        Tests the _calculate_tp_sl function for BUY and SELL scenarios.
        """
        mock_mt5_connector.get_symbol_info.return_value = self.mock_symbol_info
        mock_mt5_connector.get_account_info.return_value = self.mock_account_info

        # --- Test BUY (UP) scenario ---
        entry_price = 1.08000
        lot_size = 0.04

        # TP: 1.08000 + (2 pips * 10 * 0.00001) = 1.08000 + 0.00020 = 1.08020
        # SL: Loss = 20000 * (0.1/100) = $20.
        # Points = (20 / (0.04 * 1.0)) * 0.00001 = (500) * 0.00001 = 0.00500
        # SL price = 1.08000 - 0.00500 = 1.07500
        tp, sl = trade_manager._calculate_tp_sl("UP", entry_price, lot_size)
        self.assertAlmostEqual(tp, 1.08020)
        self.assertAlmostEqual(sl, 1.07500)

        # --- Test SELL (DOWN) scenario ---
        entry_price = 1.08000
        lot_size = 0.02

        # TP: 1.08000 - 0.00020 = 1.07980
        # SL: Loss = $20.
        # Points = (20 / (0.02 * 1.0)) * 0.00001 = (1000) * 0.00001 = 0.01000
        # SL price = 1.08000 + 0.01000 = 1.09000
        tp, sl = trade_manager._calculate_tp_sl("DOWN", entry_price, lot_size)
        self.assertAlmostEqual(tp, 1.07980)
        self.assertAlmostEqual(sl, 1.09000)


if __name__ == '__main__':
    unittest.main()
