import requests
import pandas as pd
#show all columns
pd.set_option('display.max_columns', None)

def fetch_historical_data(symbol,days=30,timeout=5):
    #fetch last 30 days of hourly prices from binance
    #returns ;dataFrame with timestamps and prices
    api_url="https://api.binance.com/api/v3/klines"

    params={
        'symbol' : symbol,
        'interval' : '1h',
        'limit' :24 * days
    } 
    response=requests.get(api_url,params)

    try:
        response= requests.get(api_url,params=params,timeout=5)
        response.raise_for_status()
        data=response.json()
            
        #dataframe
        
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close',
        'volume', 'close_time', 'quote_asset_volume',
        'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
        """
            timestamp	When the candle opened (milliseconds)
            open	Price at start of hour
            high	Highest price during hour
            low	Lowest price during hour
            close	Price at end of hour
            volume	How much BTC was traded
            close_time	When the candle closed
            quote_asset_volume	How much USDT was traded
            number_of_trades	How many trades happened
            taker_buy_base	How much BTC was bought by "takers"
            taker_buy_quote	How much USDT was spent by "takers"
            ignore	Always 0, ignore it
        """
        df['close']=pd.to_numeric(df['close'])
        df['timestamp']=pd.to_datetime(df['timestamp'],unit='ms')
        return df[['timestamp','close']]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

if __name__== "__main__":
    now=fetch_historical_data('BTCUSDT',days=30)
    print(now.head(5))