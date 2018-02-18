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
                rv.data.running = this.store[exchangeId].running;
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

    getOrdersById() {

    }

    getTradesById() {

    }

    updateTradesById() {

    }

    updateOrdersById() {

    }
}

module.exports = function(store) {
    return {
        exchangeDAO: new ExchangeDAO(store),
        exchangeCollectionDAO: new ExchangeCollectionDAO(store)
    }
}
