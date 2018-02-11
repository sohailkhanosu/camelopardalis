error_res = """{
  "error": {
    "code": 20001,
    "message": "Insufficient funds",
    "description": "Check that the funds are sufficient, given commissions"
  }
}"""

ticker_res = """[
  {
    "ask": "0.050043",
    "bid": "0.050042",
    "last": "0.050042",
    "open": "0.047800",
    "low": "0.047052",
    "high": "0.051679",
    "volume": "36456.720",
    "volumeQuote": "1782.625000",
    "timestamp": "2017-05-12T14:57:19.999Z",
    "symbol": "ETHBTC"
  },
  {
    "ask": "0.050043",
    "bid": "0.050042",
    "last": "0.050042",
    "open": "0.047800",
    "low": "0.047052",
    "high": "0.051679",
    "volume": "36456.720",
    "volumeQuote": "1782.625000",
    "timestamp": "2017-05-12T14:57:20.999Z",
    "symbol": "LTCBTC"
  }
]"""


market_trades_res = """[
  {
    "id": 9533117,
    "price": "0.046001",
    "quantity": "0.220",
    "side": "sell",
    "timestamp": "2017-04-14T12:18:40.426Z"
  },
  {
    "id": 9533116,
    "price": "0.046002",
    "quantity": "0.022",
    "side": "buy",
    "timestamp": "2017-04-14T11:56:37.027Z"
  }
]"""

orders_res = """[
  {
    "id": 840450210,
    "clientOrderId": "c1837634ef81472a9cd13c81e7b91401",
    "symbol": "ETHBTC",
    "side": "buy",
    "status": "partiallyFilled",
    "type": "limit",
    "timeInForce": "GTC",
    "quantity": "0.020",
    "price": "0.046001",
    "cumQuantity": "0.005",
    "createdAt": "2017-05-12T17:17:57.437Z",
    "updatedAt": "2017-05-12T17:18:08.610Z"
  },
  {
    "id": 123450210,
    "clientOrderId": "12345634ef81472a9cd13c81e7b91401",
    "symbol": "LTCBTC",
    "side": "buy",
    "status": "partiallyFilled",
    "type": "limit",
    "timeInForce": "GTC",
    "quantity": "0.020",
    "price": "0.046001",
    "cumQuantity": "0.005",
    "createdAt": "2017-05-12T17:17:58.437Z",
    "updatedAt": "2017-05-12T17:18:08.610Z"
  }
]"""

bid_res = """{
        "id": 0,
        "clientOrderId": "d8574207d9e3b16a4a5511753eeef175",
        "symbol": "ETHBTC",
        "side": "buy",
        "status": "new",
        "type": "limit",
        "timeInForce": "GTC",
        "quantity": "0.063",
        "price": "0.046016",
        "cumQuantity": "0.000",
        "createdAt": "2017-05-15T17:01:05.092Z",
        "updatedAt": "2017-05-15T17:01:05.092Z"
    }"""

ask_res = """{
        "id": 0,
        "clientOrderId": "d8574207d9e3b16a4a5511753eeef175",
        "symbol": "ETHBTC",
        "side": "sell",
        "status": "new",
        "type": "limit",
        "timeInForce": "GTC",
        "quantity": "0.063",
        "price": "0.046016",
        "cumQuantity": "0.000",
        "createdAt": "2017-05-15T17:01:05.092Z",
        "updatedAt": "2017-05-15T17:01:05.092Z"
    }"""

cancel_mul_res = """[{
  "id": 0,
  "clientOrderId": "d8574207d9e3b16a4a5511753eeef175",
  "symbol": "ETHBTC",
  "side": "sell",
  "status": "canceled",
  "type": "limit",
  "timeInForce": "GTC",
  "quantity": "0.000",
  "price": "0.046016",
  "cumQuantity": "0.000",
  "createdAt": "2017-05-15T17:01:05.092Z",
  "updatedAt": "2017-05-15T18:08:57.226Z"
}]"""

cancel_one_res = """{
          "id": 0,
          "clientOrderId": "d8574207d9e3b16a4a5511753eeef175",
          "symbol": "ETHBTC",
          "side": "sell",
          "status": "canceled",
          "type": "limit",
          "timeInForce": "GTC",
          "quantity": "0.000",
          "price": "0.046016",
          "cumQuantity": "0.000",
          "createdAt": "2017-05-15T17:01:05.092Z",
          "updatedAt": "2017-05-15T18:08:57.226Z"
        }"""

balance_res = """[
  {
    "currency": "BTC",
    "available": "0.0504600",
    "reserved": "0.0000000"
  },
  {
    "currency": "ETH",
    "available": "30.8504600",
    "reserved": "0.0000000"
  }
]"""

orderbook_res = """{
  "ask": [
    {
      "price": "0.046002",
      "size": "0.088"
    },
    {
      "price": "0.046800",
      "size": "0.200"
    }
  ],
  "bid": [
    {
      "price": "0.046001",
      "size": "0.005"
    },
    {
      "price": "0.046000",
      "size": "0.200"
    }
  ]
    }"""