# Q.bot - A High-Frequency Forex Scalping Bot

Q.bot is a Python-based trading bot that implements a high-frequency, Sharia-compliant scalping strategy for the EUR/USD pair on the MetaTrader 5 platform.

## Core Strategy

- **Style**: High-Frequency, Sharia-Compliant Forex Scalping (Intraday).
- **Asset**: EUR/USD.
- **Primary Goal**: Achieve a target profit of 1% of the account balance daily.
- **Profit Target per Trade**: A fixed **+2 pips**.
- **Key Constraint**: The bot will operate on a Swap-Free account. All trades **must be closed** before the end-of-day rollover to remain Sharia-compliant.

## Features

- **ML-Based Signals**: The bot's logic is designed to be driven by a sophisticated signal generation engine comprising multiple time-series models (currently a placeholder).
- **Automated Trade Management**: Automatically sets Take Profit and Stop Loss for all trades.
- **Manual Trade Supervision**: Monitors and manages manually opened trades to enforce risk parameters.
- **Configurable**: All major parameters can be configured in `q_bot/config.py`.

## Getting Started

### Prerequisites

- Python 3.8+
- MetaTrader 5 Terminal
- A Swap-Free trading account

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd q.bot
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. Open `q_bot/config.py` in a text editor.
2. Fill in your MetaTrader 5 account credentials and specify the path to the terminal.
3. Adjust any other trading parameters as needed.

### Running the Bot

Ensure your MetaTrader 5 terminal is running. Then, execute the following command:

```bash
python -m q_bot.main
```

## Disclaimer

Trading foreign exchange on margin carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Before deciding to trade foreign exchange you should carefully consider your investment objectives, level of experience, and risk appetite. The possibility exists that you could sustain a loss of some or all of your initial investment and therefore you should not invest money that you cannot afford to lose. You should be aware of all the risks associated with foreign exchange trading, and seek advice from an independent financial advisor if you have any doubts. Any opinions, news, research, analyses, prices, or other information contained on this website is provided as general market commentary, and does not constitute investment advice.
