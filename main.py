import ccxt
import config
import keys

#print(ccxt.exchanges) 
print('Sandbox mode:', config.sandbox)

exchange_id = config.exchange_id
exchange_class = getattr(ccxt, exchange_id)

# Instiate real or test exchange

if config.sandbox:
    exchange = exchange_class({
        'apiKey': keys.keyList[exchange_id]['api_test'],
        'secret': keys.keyList[exchange_id]['secret_test'],
        'enableRateLimit': True,
    })
    exchange.set_sandbox_mode(True)
else:
    exchange = exchange_class({
        'apiKey': keys.keyList[exchange_id]['api'],
        'secret': keys.keyList[exchange_id]['secret'],
    })

# Load markets
markets = exchange.load_markets()

#print(markets.keys())
#print(exchange.markets['ETH/BTC'])


input('Press Enter to continue...')