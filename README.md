# Coinbase Market Analyzer

A Python-based tool for analyzing cryptocurrency trading opportunities on Coinbase using technical indicators and market data.

## Overview

This tool connects to the Coinbase Exchange API to analyze cryptocurrency trading pairs, identifying potential trading opportunities based on various technical indicators including RSI (Relative Strength Index), volume trends, and volatility patterns.

## Features

- Real-time market data retrieval from Coinbase Exchange
- Analysis of USD trading pairs
- Technical indicators calculation:
  - RSI (Relative Strength Index)
  - Volume trends
  - Volatility analysis
- Customizable volume thresholds for filtering
- Automatic scanning of all available trading pairs
- Rate limit handling for API requests

## Technical Indicators

The analyzer evaluates trading pairs based on several key metrics:

- **RSI (Relative Strength Index)**: Identifies oversold conditions (RSI < 30)
- **Volume Trend**: Spots unusual trading activity (>2x average volume)
- **Volatility**: Tracks price volatility relative to historical averages

## Requirements

```
requests
pandas
numpy
```

## Installation

1. Clone this repository:
```bash
git clone [your-repository-url]
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

To run the market analyzer:

```python
python coinbase_analyzer.py
```

The script will:
1. Connect to Coinbase Exchange API
2. Retrieve available trading pairs
3. Filter for USD pairs with sufficient volume
4. Analyze each pair using technical indicators
5. Output potential trading opportunities

## Configuration

You can modify the following parameters in the script:

- `min_volume`: Minimum 24-hour trading volume (default: 100,000 USD)
- `granularity`: Timeframe for historical data (default: 3600 seconds/1 hour)
- Technical indicator thresholds:
  - RSI oversold threshold: 30
  - Volume trend multiplier: 2.0

## Output Example

```
Product: BTC-USD
Current Price: $50,000.00
24h Volume: $1,500,000.00
Indicators:
- oversold
- high_volume
--------------------------------------------------
```

## Class Structure

### CoinbaseAnalyzer

Main class containing all analysis functionality:

- `get_products()`: Retrieves available trading pairs
- `get_product_stats()`: Gets 24-hour statistics for a trading pair
- `get_historical_data()`: Retrieves historical price data
- `calculate_metrics()`: Computes technical indicators
- `scan_for_opportunities()`: Analyzes all pairs for trading opportunities

## Error Handling

The tool includes comprehensive error handling for:
- API connection issues
- Data parsing errors
- Rate limit management
- Insufficient data scenarios

## API Rate Limits

The tool implements a 0.5-second delay between requests to respect Coinbase API rate limits.

## Disclaimer

This tool is for informational purposes only. Cryptocurrency trading carries significant risks, and past performance does not indicate future results. Always conduct your own research before making trading decisions.


## Contributing

Feel free to open issues or submit pull requests with improvements.
