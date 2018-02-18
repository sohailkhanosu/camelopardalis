/* data abstraction layer */

class ExchangeCollectionDAO {
    constructor(store) {
        this.store = store;
    }

    addExchange(exchangeId) {
        /* add the exchange to the list of supported exchanges */
        if (! this.store.hasOwnProperty(exchangeId))
            this.store[exchangeId] = {};
    }

    /* diff the given state with the current state
     * expecting an object that contains new state for
     * given exchanges
     * ie: {'poloniex': {true, 'exmo': false, ...}
     * */
    updateState(newState) {}

    /* return the status for all the exchanges */
    getStatus() {
        return new Promise((resolve, reject) => {
            let rv = {};
            rv.data = {};
            Object.keys(this.store).forEach(exchangeId => {
                rv.data[exchangeId] = {};
                rv.data[exchangeId].markets = Object.assign({}, this.store[exchangeId].markets);
                rv.data[exchangeId].strategy = this.store[exchangeId].strategy;
                rv.data[exchangeId].running = this.store[exchangeId].running;
                // TODO: deep copy these or just do json.stringify/parse
                rv.data[exchangeId].balances = this.store[exchangeId].balances;
                rv.data[exchangeId].activeOrders = this.store[exchangeId].orders || [];
                rv.data[exchangeId].trades = this.store[exchangeId].trades || [];
            });
            /* typeify the message */
            rv.type = 'status-all';
            resolve(rv);
        })
    }
}

class ExchangeDAO {
   /* one exchange */
    constructor(store) {
        this.store = store;
    }

    findExchangeById(exchangeId) {
        return new Promise((resolve, reject) => {
            if (exchangeId in this.store) {
                return resolve(this.store[exchangeId]);
            }
            return reject(`exchange ${exchangeId} not found`);
        })
    }

    /* replace the data for the given exchange with the given data
     * omitted data does not result in data erasure
     * */
    updateExchange(exchangeId, data) {
        this.findExchangeById(exchangeId)
            .then((exchange) => {
                /* diff the data with current exchange data */
                exchange.strategy = data.strategy;
                exchange.markets = Object.assign({}, data.markets);
            })
            .catch((err) => console.log(err))
    }

    /* update exchange running state (is the script running?) */
    updateExchangeRunningState(exchangeId, isRunning) {
        this.findExchangeById(exchangeId)
            .then((exchange) => {
                exchange.running = isRunning;
            })
            .catch((err) => console.log(err))
    }

    getBalances(exchangeId) {
        return new Promise((resolve, reject) => {
            this.findExchangeById(exchangeId)
                .then(exchange => resolve(exchange.balances))
                .catch(err => console.log(err))
        })
    }

    getOrders(exchangeId) {
        return new Promise((resolve, reject) => {
            this.findExchangeById(exchangeId)
                .then(exchange => resolve(exchange.orders))
                .catch(err => console.log(err))
        })
    }

    getTrades(exchangeId) {
        return new Promise((resolve, reject) => {
            this.findExchangeById(exchangeId)
                .then(exchange => resolve(exchange.trades))
                .catch(err => console.log(err))
        })
    }

    updateBalances(exchangeId, newBalance) {
        this.findExchangeById(exchangeId)
            .then(exchange => {
                exchange.balances = newBalance;
            })
            .catch(err => console.log(err))
    }

    updateOrders(exchangeId, orders) {
        this.findExchangeById(exchangeId)
            .then(exchange => {
                exchange.orders = orders;
            })
            .catch(err => console.log(err))
    }

    updateTrades(exchangeId, trades) {
        this.findExchangeById(exchangeId)
            .then(exchange => {
                exchange.trades = trades;
            })
            .catch(err => console.log(err))
    }
}

module.exports = function(store) {
    return {
        exchangeDAO: new ExchangeDAO(store),
        exchangeCollectionDAO: new ExchangeCollectionDAO(store)
    }
}
