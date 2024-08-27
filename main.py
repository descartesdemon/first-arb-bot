import ccxt
import math
import config
import keys
import time
import collections
import asyncio


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

def build_graph_tickers(graph, tickers):
    '''Deprecated; use build_graph_order_books instead because of rate limiting and lack of support for all exchanges'''
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

def build_graph_order_books(graph, order_books):
    for order_book in order_books:
        base, quote = order_book['symbol'].split('/')
        if base not in graph or quote not in graph:
            continue
        # Buyer bids to buy base w/ quote; we sell to buyer base for quote
        if order_book['bids']:
            graph[base][quote] = {
                'rate': order_book['bids'][0][0],
                'weight': -math.log(order_book['bids'][0][0]), # negative log transform so arbitrage opportunities become detectable negative cycles; r1 * r2 * r3 > 1 implies -log(r1) - log(r2) - log(r3) < 0
                'type': 'bid',
                'quantity': order_book['bids'][0][1],
            }
        # Seller asks to sell base for quote; we buy base using our quote
        if order_book['asks']:
            graph[quote][base] = {
                'rate': order_book['asks'][0][0],
                'weight': -math.log(1/order_book['asks'][0][0]),
                'type': 'ask',
                'quantity': order_book['asks'][0][1],
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
                #print('Negative cycle detected!')
                
                # find vertex in cycle
                #visited = dict((cur, False) for cur in graph)
                visited = dict.fromkeys(graph, False)
                visited[neighbor] = True
                while not visited[currency]:
                    visited[currency] = True
                    currency = predecessors[currency]

                # reconstruct cycle
                #negative_cycle = [currency]
                negative_cycle = collections.deque([currency])
                #print(negative_cycle)
                neighbor = predecessors[currency]
                while currency != neighbor:
                    #negative_cycle.append(neighbor)
                    negative_cycle.appendleft(neighbor)
                    #print(negative_cycle)
                    #print(neighbor, predecessors[neighbor])
                    neighbor = predecessors[neighbor]
                #negative_cycle = negative_cycle[::-1]
                print('ARBITRAGE:', negative_cycle)

                for i in range(len(negative_cycle)):
                    print(negative_cycle[i], '->', negative_cycle[(i + 1) % len(negative_cycle)], 'at transformed rate', graph[negative_cycle[i]][negative_cycle[(i + 1) % len(negative_cycle)]]['weight'])
                print('Total rate:', math.exp(-sum([graph[negative_cycle[i]][negative_cycle[(i + 1) % len(negative_cycle)]]['weight'] for i in range(len(negative_cycle))])))
                return negative_cycle
    return []

def create_arbitrage_path(graph, cycle, base_curr):
    # need to find best way to go from base_curr to any other currency in cycle
    # if base_curr is in cycle, return cycle but rotate s.t. base_curr is first
    return_cycle = cycle
    if base_curr in cycle:
        return_cycle.rotate(-cycle.index(base_curr))
        return_cycle.append(base_curr)
        return return_cycle
    else:
    # if base_curr is not in cycle, find best way to go from base_curr to cycle
        best_rate = math.inf
        best = None
        for curr in return_cycle:
            # maybe find a more elegant solution
            if base_curr in graph[curr] and curr in graph[base_curr]: # check if 2-way path between base and the candidate
                # TODO: complete this
                if graph[base_curr][curr]['weight'] + graph[curr][base_curr]['weight'] < best_rate:
                    best_rate = graph[base_curr][curr]['weight']
                    best = curr
        if best is not None:
            return_cycle.rotate(-cycle.index(best))
            return_cycle.appendleft(base_curr)
            return_cycle.append(base_curr)
            return return_cycle
    return None

def execute_arbitrage_path(path):
    ...

async def fetch_individual_ob(exchange, ticker):
    return exchange.fetch_order_book(ticker)

async def fetch_order_books_list(exchange, ticker_list):
    return await asyncio.gather(*[fetch_individual_ob(exchange, ticker) for ticker in ticker_list])


async def main():
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


    home_currency = config.home_currency
    home_balance = exchange.fetch_balance()[home_currency]

    print('Balance of', home_currency, ':', home_balance)

    valid_input = False
    valid_currencies = exchange.currencies.keys()

    print('Valid currencies:', *valid_currencies)

    while not valid_input:
        input_currencies_string = input('Enter comma-separated list of currencies to track: ')
        input_currencies = input_currencies_string.split(',')
        input_currencies = [currency.strip() for currency in input_currencies]
        valid_input = True
        for currency in input_currencies:
            if currency not in valid_currencies:
                print('Invalid currency: ' + currency + '!')
                valid_input = False
        
    # Initialize graph for bellman-ford
    graph = {currency: {} for currency in input_currencies}

    ## Populate initial graph using fetchOrderBooks
    ticker_list = exchange.fetchTickers().keys()
    filtered_list = list(filter(lambda t: t.split('/')[0] in input_currencies and t.split('/')[1] in input_currencies, ticker_list))

    all_order_books = await fetch_order_books_list(exchange, filtered_list)

    while True:
        all_order_books = await fetch_order_books_list(exchange, filtered_list)
        build_graph_order_books(graph, all_order_books)
        #print(find_arbitrage_cycle(graph, home_currency)) #Pick arbitrary starting currency
        print('PATH:', create_arbitrage_path(graph, find_arbitrage_cycle(graph, home_currency), home_currency))
        time.sleep(0.5)

    input('Press Enter to continue...')

asyncio.run(main())