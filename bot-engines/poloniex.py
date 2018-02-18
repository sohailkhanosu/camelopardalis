import sys
import random
import json
import datetime
import time

from typing import List


def trades_generator():
    while True:
        yield {
            'type': 'trades',
            'exchange': 'poloniex',
            'data': {
                'trades': [
                    {'type': 'sell' if random.random() > 0.5 else 'buy',
                     'market': 'ETH_BTC' if random.random() > 0.5 else 'BCC_BTC',
                     'amount': random.random(),
                     'rate': 1000 * random.random(),
                     'date': datetime.datetime.now().isoformat()
                    }
                    for _ in range(random.randint(1, 10))
                ]
            }
        }


def get_balance(total=100):
    percentage_free = random.random() * 0.5
    available = total * percentage_free
    return {'available': available, 'locked': total - available, 'total': total}


def balances_generator():
    while True:
        yield {
            'type': 'balance',
            'exchange': 'poloniex',
            'data': {
                'balances': {
                    'ETH': get_balance(),
                    'BTC': get_balance(),
                    'BCC': get_balance()
                }
            }
        }

def status_generator():
    while True:
        yield {
            'type': 'status',
            'exchange': 'poloniex',
            'data': {
                'strategy': 'Basic',
                'markets': {
                    'ETH_BTC': random.random() > 0.10,
                    'BCC_BTC': random.random() > 0.10
                }
            }
        }


def main(args: List[str]) -> None:
    generators = [trades_generator(), balances_generator(), status_generator()]
    
    # prime generators
    for gen in generators:
        next(gen)

    while True:
        # print the status one at each loop
        print(json.dumps(next(generators[-1])), flush=True)
        try:
            received_data = json.loads(input())
        except Exception:
            print(json.dumps({'type': 'error', 'data': 'unable to read value shutting down'}))
            return 1

        if received_data.get('type') == 'shutdown':
            return 0
        elif received_data.get('type') == 'ping':
            print(json.dumps({'type': 'pong', 'data': received_data['data'], 'exchange': 'exmo'}), flush=True)
        print(json.dumps(next(generators[random.randint(0, 1)])), flush=True)
        time.sleep(random.random() * 5)     # sleep between 0 -5 seconds


if __name__ == '__main__':
    main(sys.argv)
