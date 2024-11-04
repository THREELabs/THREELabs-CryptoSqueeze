# Part 1: Core functionality
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

class CoinbaseAnalyzer:
    def __init__(self):
        self.base_url = "https://api.exchange.coinbase.com"
        self.recommended_pairs = ['ETH-USD', 'SOL-USD', 'MATIC-USD']
        
    def get_products(self):
        """Get list of available trading pairs"""
        try:
            response = requests.get(f"{self.base_url}/products")
            print(f"API Status Code: {response.status_code}")
            
            if response.status_code == 200:
                products = response.json()
                print(f"Found {len(products)} total products")
                return products
            else:
                print(f"Error response: {response.text}")
                return []
        except Exception as e:
            print(f"Error fetching products: {str(e)}")
            return []

    def get_product_stats(self, product_id):
        """Get 24hr stats for a specific trading pair"""
        try:
            response = requests.get(f"{self.base_url}/products/{product_id}/stats")
            if response.status_code == 200:
                return response.json()
            print(f"Error getting stats for {product_id}: {response.text}")
            return None
        except Exception as e:
            print(f"Error getting stats for {product_id}: {str(e)}")
            return None

    def get_historical_data(self, product_id, start, end, granularity=3600):
        """Get historical price data"""
        try:
            params = {
                'start': start.isoformat(),
                'end': end.isoformat(),
                'granularity': granularity
            }
            response = requests.get(f"{self.base_url}/products/{product_id}/candles", params=params)
            
            if response.status_code != 200:
                print(f"Error getting historical data for {product_id}: {response.text}")
                return None
                
            data = response.json()
            
            if not isinstance(data, list) or len(data) < 20:
                print(f"Insufficient historical data for {product_id}")
                return None
                
            return data
            
        except Exception as e:
            print(f"Error getting historical data for {product_id}: {str(e)}")
            return None

# Part 2: Analysis Methods
    def calculate_metrics(self, data):
        """Calculate technical indicators"""
        try:
            # Convert to DataFrame and handle reverse chronological order
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.sort_values('time')
            
            # Calculate RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Calculate volume trend
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_trend'] = df['volume'] / df['volume_sma']
            
            # Calculate volatility
            df['volatility'] = df['close'].pct_change().rolling(window=20).std()
            
            return df
            
        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            return None

    def calculate_price_momentum(self, df):
        """Calculate price momentum indicators"""
        try:
            # Calculate EMA crossovers
            df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
            df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
            
            latest = df.iloc[-1]
            momentum = {
                'ema_trend': 'bullish' if latest['EMA20'] > latest['EMA50'] else 'bearish',
                'strength': abs(latest['EMA20'] - latest['EMA50']) / latest['EMA50'] * 100
            }
            
            return momentum
            
        except Exception as e:
            print(f"Error calculating price momentum: {str(e)}")
            return None

    def calculate_support_resistance(self, df):
        """Calculate support and resistance levels"""
        try:
            # Simple support/resistance based on recent price action
            recent_df = df.tail(30)  # Last 30 periods
            
            support = recent_df['low'].mean() - recent_df['low'].std()
            resistance = recent_df['high'].mean() + recent_df['high'].std()
            
            return {
                'support': support,
                'resistance': resistance
            }
            
        except Exception as e:
            print(f"Error calculating support/resistance: {str(e)}")
            return None

    def calculate_trend_strength(self, df):
        """Calculate trend strength using ADX-like calculation"""
        try:
            # Simplified ADX calculation
            df['TR'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            
            df['DM_plus'] = np.where(
                (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                np.maximum(df['high'] - df['high'].shift(1), 0),
                0
            )
            
            df['DM_minus'] = np.where(
                (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                np.maximum(df['low'].shift(1) - df['low'], 0),
                0
            )
            
            # Calculate trend strength (simplified ADX)
            period = 14
            df['TR_avg'] = df['TR'].rolling(window=period).mean()
            df['DI_plus'] = df['DM_plus'].rolling(window=period).mean() / df['TR_avg'] * 100
            df['DI_minus'] = df['DM_minus'].rolling(window=period).mean() / df['TR_avg'] * 100
            
            latest = df.iloc[-1]
            
            return {
                'strength': abs(latest['DI_plus'] - latest['DI_minus']),
                'direction': 'bullish' if latest['DI_plus'] > latest['DI_minus'] else 'bearish'
            }
            
        except Exception as e:
            print(f"Error calculating trend strength: {str(e)}")
            return None

    def scan_for_opportunities(self, min_volume=10000):
        """Scan for potential opportunities based on technical indicators"""
        opportunities = []
        
        # Get all available trading pairs
        products = self.get_products()
        if not products:
            print("No products found to analyze")
            return opportunities
        
        print(f"\nAnalyzing {len(products)} products...")
        
        for product in products:
            try:
                product_id = product.get('id')
                if not product_id:
                    continue
                
                # Only analyze USD trading pairs with sufficient volume
                if not product_id.endswith('-USD'):
                    continue
                
                print(f"\nAnalyzing {product_id}...")
                
                # Get recent stats
                stats = self.get_product_stats(product_id)
                if not stats:
                    continue
                    
                volume = float(stats.get('volume', 0))
                if volume < min_volume:
                    print(f"Skipping {product_id} - insufficient volume: ${volume:,.2f}")
                    continue
                
                print(f"24h Volume: ${volume:,.2f}")
                
                # Get historical data
                end = datetime.now()
                start = end - timedelta(days=7)
                historical_data = self.get_historical_data(product_id, start, end)
                
                if not historical_data:
                    continue
                
                # Calculate metrics
                df = self.calculate_metrics(historical_data)
                if df is None or df.empty:
                    continue
                
                latest = df.iloc[-1]
                
                # Check for significant indicators
                conditions = {}
                
                if pd.notnull(latest['RSI']):
                    conditions['oversold'] = latest['RSI'] < 30
                    print(f"RSI: {latest['RSI']:.2f}")
                
                if pd.notnull(latest['volume_trend']):
                    conditions['high_volume'] = latest['volume_trend'] > 2.0
                    print(f"Volume Trend: {latest['volume_trend']:.2f}x average")
                
                if pd.notnull(latest['volatility']):
                    conditions['increasing_volatility'] = latest['volatility'] > df['volatility'].mean()
                    print(f"Volatility: {latest['volatility']:.2f}")
                
                if any(conditions.values()):
                    print(f"Found opportunity in {product_id}!")
                    opportunities.append({
                        'product_id': product_id,
                        'price': latest['close'],
                        'volume': volume,
                        'indicators': conditions
                    })
                
                # Respect API rate limits
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error analyzing {product_id if 'product_id' in locals() else 'unknown'}: {str(e)}")
                continue
        
        return opportunities

    def analyze_recommended_pairs(self):
        """Detailed analysis of recommended trading pairs"""
        recommendations = []
        
        for pair in self.recommended_pairs:
            try:
                analysis = self.detailed_pair_analysis(pair)
                if analysis:
                    recommendations.append(analysis)
                time.sleep(0.5)  # Respect rate limits
            except Exception as e:
                print(f"Error analyzing {pair}: {str(e)}")
                
        return recommendations

    def detailed_pair_analysis(self, product_id):
        """Perform detailed analysis on a specific trading pair"""
        try:
            # Get current stats
            stats = self.get_product_stats(product_id)
            if not stats:
                return None
                
            # Get historical data for different timeframes
            end = datetime.now()
            day_data = self.get_historical_data(product_id, end - timedelta(days=1), end, 300)  # 5-min candles
            week_data = self.get_historical_data(product_id, end - timedelta(days=7), end, 3600)  # 1-hour candles
            month_data = self.get_historical_data(product_id, end - timedelta(days=30), end, 86400)  # 1-day candles
            
            if not all([day_data, week_data, month_data]):
                return None
                
            # Calculate metrics for different timeframes
            day_metrics = self.calculate_metrics(day_data)
            week_metrics = self.calculate_metrics(week_data)
            month_metrics = self.calculate_metrics(month_data)
            
            if not all([day_metrics, week_metrics, month_metrics]):
                return None
                
            # Get the latest metrics
            latest_day = day_metrics.iloc[-1]
            latest_week = week_metrics.iloc[-1]
            latest_month = month_metrics.iloc[-1]
            
            # Calculate additional metrics
            price_momentum = self.calculate_price_momentum(month_metrics)
            support_resistance = self.calculate_support_resistance(month_metrics)
            trend_strength = self.calculate_trend_strength(month_metrics)
            
            return {
                'product_id': product_id,
                'current_price': latest_day['close'],
                'volume_24h': float(stats.get('volume', 0)),
                'metrics': {
                    'short_term': {
                        'rsi': latest_day['RSI'],
                        'volume_trend': latest_day['volume_trend'],
                        'volatility': latest_day['volatility']
                    },
                    'medium_term': {
                        'rsi': latest_week['RSI'],
                        'volume_trend': latest_week['volume_trend'],
                        'volatility': latest_week['volatility']
                    },
                    'long_term': {
                        'rsi': latest_month['RSI'],
                        'volume_trend': latest_month['volume_trend'],
                        'volatility': latest_month['volatility']
                    }
                },
                'analysis': {
                    'price_momentum': price_momentum,
                    'support_level': support_resistance['support'],
                    'resistance_level': support_resistance['resistance'],
                    'trend_strength': trend_strength
                }
            }
            
        except Exception as e:
            print(f"Error in detailed analysis for {product_id}: {str(e)}")
            return None


# Part 3: Main execution code

def main():
    analyzer = CoinbaseAnalyzer()
    print("Starting market analysis...")
    
    # Get general market opportunities
    opportunities = analyzer.scan_for_opportunities(min_volume=100000)
    
    if opportunities:
        print(f"\nFound {len(opportunities)} general market opportunities:")
        for opp in opportunities:
            print(f"\nProduct: {opp['product_id']}")
            print(f"Current Price: ${opp['price']:,.2f}")
            print(f"24h Volume: ${opp['volume']:,.2f}")
            print("Indicators:")
            for indicator, value in opp['indicators'].items():
                if value:
                    print(f"- {indicator}")
            print("-" * 50)
    
    # Analyze recommended pairs
    print("\nAnalyzing recommended cryptocurrency pairs...")
    recommendations = analyzer.analyze_recommended_pairs()
    
    if recommendations:
        print("\nDetailed Analysis of Recommended Cryptocurrencies:")
        for rec in recommendations:
            print(f"\n{rec['product_id']} Analysis:")
            print(f"Current Price: ${rec['current_price']:,.2f}")
            print(f"24h Volume: ${rec['volume_24h']:,.2f}")
            
            print("\nTechnical Metrics:")
            print("Short-term (24h):")
            print(f"- RSI: {rec['metrics']['short_term']['rsi']:.2f}")
            print(f"- Volume Trend: {rec['metrics']['short_term']['volume_trend']:.2f}x")
            print(f"- Volatility: {rec['metrics']['short_term']['volatility']:.2f}")
            
            print("\nMedium-term (7d):")
            print(f"- RSI: {rec['metrics']['medium_term']['rsi']:.2f}")
            print(f"- Volume Trend: {rec['metrics']['medium_term']['volume_trend']:.2f}x")
            print(f"- Volatility: {rec['metrics']['medium_term']['volatility']:.2f}")
            
            print("\nLong-term (30d):")
            print(f"- RSI: {rec['metrics']['long_term']['rsi']:.2f}")
            print(f"- Volume Trend: {rec['metrics']['long_term']['volume_trend']:.2f}x")
            print(f"- Volatility: {rec['metrics']['long_term']['volatility']:.2f}")
            
            print("\nPrice Analysis:")
            print(f"- Momentum: {rec['analysis']['price_momentum']['ema_trend']} "
                  f"(Strength: {rec['analysis']['price_momentum']['strength']:.2f})")
            print(f"- Trend: {rec['analysis']['trend_strength']['direction']} "
                  f"(Strength: {rec['analysis']['trend_strength']['strength']:.2f})")
            print(f"- Support Level: ${rec['analysis']['support_level']:,.2f}")
            print(f"- Resistance Level: ${rec['analysis']['resistance_level']:,.2f}")
            
            print("-" * 50)
    else:
        print("\nNo detailed analysis available for recommended pairs.")

if __name__ == "__main__":
    main()
