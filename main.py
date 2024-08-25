import ccxt
import math
import config
import keys

def get_exchange_id():
    exchange_id = input('Enter exchange id: ')
    while exchange_id not in ccxt.exchanges:
        print('Invalid exchange id. Please enter a valid exchange id.')
        exchange_id = input('Enter exchange id: ')
    return exchange_id

def build_graph(graph, tickers):
    for pair in tickers:
        ticker = tickers[pair]
        base, quote = pair.split('/')
        if base not in graph or quote not in graph:
            continue
        # Buyer bids to buy base w/ quote; we sell to buyer base for quote
        if ticker['bid']:
            graph[base][quote] = {
                'rate': ticker['bid'],
                'weight': -math.log(ticker['bid']), # negative log transform so arbitrage opportunities become detectable negative cycles; r1 * r2 * r3 > 1 implies -log(r1) - log(r2) - log(r3) < 0
                'type': 'bid',
                'quantity': ticker['bidVolume'],
            }
        # Seller asks to sell base for quote; we buy base using our quote
        if ticker['ask']:
            graph[quote][base] = {
                'rate': ticker['ask'],
                'weight': -math.log(1/ticker['ask']),
                'type': 'ask',
                'quantity': ticker['askVolume'],
            }

#print(ccxt.exchanges) 
print('Sandbox mode:', config.sandbox)

exchange_id = config.exchange_id
exchange_class = getattr(ccxt, exchange_id)

# Instantiate real or test exchange

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
        'enableRateLimit': True,
    })

# Load markets
markets = exchange.load_markets()

#print(exchange.fetchTickers(['ETH/BTC']))
#print(exchange.fetchTickers().keys())
#print(exchange.currencies.keys())

# Initialize graph for bellman-ford
graph = {}
for currency in exchange.currencies.keys():
    graph[currency] = {}

# Populate initial graph
tickers = exchange.fetchTickers()
build_graph(graph, tickers)

#print(graph['BTC']['ETH'])
#print(graph['ETH']['BTC'])

#print(graph['BTC']['ETH']['weight'] + graph['ETH']['LTC']['weight'] + graph['LTC']['BTC']['weight'])

#print(markets.keys())
#print(exchange.markets['ETH/BTC'])
#print(exchange.fetch_balance()['BTC'])
#print(exchange.fetch_order_book('ETH/BTC'))

home_currency = config.home_currency
home_balance = exchange.fetch_balance()[home_currency]

print('Balance of', home_currency, ':', home_balance)


### Pseudocode
#while True
#    get balance
#    get order book
#    build graph of exchange rates for bellman ford (how do we account for depth??)
#       preliminary graph building algo:
#       get best exchange rates between assets
#       cap quantity traded by max(available balance, bid/ask quantity)
#       rebuild graph (naive approach? maybe just update weights)
#       
#
#
#
#
#


input('Press Enter to continue...')