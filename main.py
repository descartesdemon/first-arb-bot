import ccxt
import math
import config
import keys
import time
import collections


test_graph = {
    'A': {
        'B': {'weight': -math.log(1.2), 'type': 'bid', 'quantity': 100},
        'C': {'weight': -math.log(0.9), 'type': 'ask', 'quantity': 100},
        'D': {'weight': -math.log(0.95), 'type': 'ask', 'quantity': 100},
        'E': {'weight': -math.log(0.98), 'type': 'ask', 'quantity': 100},
    },
    'B': {
        'A': {'weight': -math.log(0.83), 'type': 'ask', 'quantity': 100},
        'C': {'weight': -math.log(1.1), 'type': 'bid', 'quantity': 100},
        'D': {'weight': -math.log(1.05), 'type': 'bid', 'quantity': 100},
        'E': {'weight': -math.log(1.02), 'type': 'bid', 'quantity': 100},
    },
    'C': {
        'A': {'weight': -math.log(1.1), 'type': 'bid', 'quantity': 100},
        'B': {'weight': -math.log(0.9), 'type': 'ask', 'quantity': 100},
        'D': {'weight': -math.log(0.96), 'type': 'ask', 'quantity': 100},
        'E': {'weight': -math.log(0.99), 'type': 'ask', 'quantity': 100},
    },
    'D': {
        'A': {'weight': -math.log(1.05), 'type': 'bid', 'quantity': 100},
        'B': {'weight': -math.log(0.95), 'type': 'ask', 'quantity': 100},
        'C': {'weight': -math.log(1.04), 'type': 'bid', 'quantity': 100},
        'E': {'weight': -math.log(1.03), 'type': 'bid', 'quantity': 100},
    },
    'E': {
        'A': {'weight': -math.log(1.02), 'type': 'bid', 'quantity': 100},
        'B': {'weight': -math.log(0.98), 'type': 'ask', 'quantity': 100},
        'C': {'weight': -math.log(1.01), 'type': 'bid', 'quantity': 100},
        'D': {'weight': -math.log(0.97), 'type': 'ask', 'quantity': 100},
    },
}

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

def find_arbitrage_cycle(graph, begin):
    """Takes a graph of exchange rates and a starting currency, and finds an arbitrage opportunity (negative cycle) using Bellman-Ford algorithm. Begin should be a currency in the graph preferably connected to many other currencies. Returns as a deque containing an arbitrage cycle."""
    if begin not in graph:
        print('Invalid currency for Bellman-Ford: ' + begin + '!')
        return
    
    distances = {}
    predecessors = {}

    for currency in graph:
        distances[currency] = math.inf
        predecessors[currency] = None
    distances[begin] = 0

    for i in range(len(graph) - 1):
        for currency in graph:
            for neighbor in graph[currency]:
                if distances[currency] + graph[currency][neighbor]['weight'] < distances[neighbor]:
                    distances[neighbor] = distances[currency] + graph[currency][neighbor]['weight']
                    predecessors[neighbor] = currency

# reconstruct negative cycles

    for currency in graph:
        for neighbor in graph[currency]:
            if distances[currency] + graph[currency][neighbor]['weight'] < distances[neighbor]:
                print('Negative cycle detected!')
                
                # find vertex in cycle
                visited = dict((cur, False) for cur in graph)
                visited[neighbor] = True
                while not visited[currency]:
                    visited[currency] = True
                    currency = predecessors[currency]

                # reconstruct cycle
                #negative_cycle = [currency]
                negative_cycle = collections.deque([currency])
                print(negative_cycle)
                neighbor = predecessors[currency]
                while currency != neighbor:
                    #negative_cycle.append(neighbor)
                    negative_cycle.appendleft(neighbor)
                    print(negative_cycle)
                    print(neighbor, predecessors[neighbor])
                    neighbor = predecessors[neighbor]
                #negative_cycle = negative_cycle[::-1]
                print('ARBITRAGE:', negative_cycle)

                for i in range(len(negative_cycle)):
                    print(negative_cycle[i], '->', negative_cycle[(i + 1) % len(negative_cycle)], 'at transformed rate', graph[negative_cycle[i]][negative_cycle[(i + 1) % len(negative_cycle)]]['weight'])
                print('Total rate:', math.exp(-sum([graph[negative_cycle[i]][negative_cycle[(i + 1) % len(negative_cycle)]]['weight'] for i in range(len(negative_cycle))])))
                return negative_cycle
    return []

def create_arbitrage_path(cycle, base_curr):
    # need to find best way to go from base_curr to any other currency in cycle
    # if base_curr is in cycle, return cycle but rotate s.t. base_curr is first
    if base_curr in cycle:
        return cycle.rotate(-cycle.index(base_curr))
    else:
    # if base_curr is not in cycle, find best way to go from base_curr to cycle
        for curr in cycle:
            best = math.inf


#print(ccxt.exchanges) 
print('Sandbox mode:', config.sandbox)

exchange_id = config.exchange_id
exchange_class = getattr(ccxt, exchange_id)

# Instantiate real or test exchange

if config.sandbox:
    exchange = exchange_class(keys.keyDict_sandbox[exchange_id])
    exchange.enableRateLimit = True
    exchange.set_sandbox_mode(True)
else:
    exchange = exchange_class(keys.KeyDict[exchange_id])
    exchange.enableRateLimit = True

# Load markets
markets = exchange.load_markets()

#print(exchange.fetchTradingFees())

#print(markets['ETH/BTC'])

#print(exchange.fetchTickers(['ETH/BTC']))
#print(exchange.fetchTickers().keys())
#print(exchange.currencies.keys())

# Initialize graph for bellman-ford
graph = {}
for currency in exchange.currencies.keys():
    graph[currency] = {}

# Populate initial graph
tickers = exchange.fetchTickers()
#print(tickers.keys())
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


#print(graph)
while True:
    tickers = exchange.fetchTickers()
    build_graph(graph, tickers)
    print(find_arbitrage_cycle(graph, 'BTC')) #Pick arbitrary starting currency
    time.sleep(0.5)


# The arbitrage opportunity is A -> B -> C -> A
# A -> B at a rate of 1.2 (sell A to buy B)
# B -> C at a rate of 1.1 (sell B to buy C)
# C -> A at a rate of 1.1 (sell C to buy A)
# The total rate is 1.2 * 1.1 * 1.1 = 1.452, which is greater than 1, so there's an arbitrage opportunity.


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