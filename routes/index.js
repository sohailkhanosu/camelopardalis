const express = require('express');
const router = express.Router();
const store = require('../store');
const daos = require('../dao')(store);
const bs = require('../botSpawner')({}, true, daos);

/* GET home page. */
router.get('/', function(req, res, next) {
  res.sendFile(__dirname + '/public/index.html');
});

router.get('/state', function(req, res, next) {
    daos.exchangeCollectionDAO.getStatus()
        .then((data) => res.json(data));
});

/* allow client to shutoff bots {'data': {'poloniex': true, 'exmo': false, ...}}*/
router.post('/state', function(req, res, next) {
    let data = req.body.data;
    Object.keys(data).forEach((exchangeId) => {
        if (data[exchangeId]) {
            bs.startBot(exchangeId);
        } else {
            bs.stopBot(exchangeId);
        }
    });
    daos.exchangeCollectionDAO.getStatus()
        .then((data) => res.json(data));
});

router.post('/update', function(req, res, next) {
    let message = req.body.data;
    /* TODO: temporary message processing code;
     * its fine after pass-through but switch statement here
     * should be replaced with a function */
    switch (message.type) {
        case 'status':
            bs.daos.exchangeDAO.updateExchange(message.exchange, message.data);
            break;
        case 'balance':
            bs.daos.exchangeDAO.updateBalances(message.exchange, message.data);
            break;
        case 'active_orders':
            bs.daos.exchangeDAO.updateOrders(message.exchange, message.data);
            break;
        case 'trades':
            bs.daos.exchangeDAO.updateTrades(message.exchange, message.data);
            break;
        case 'orderbooks':
            bs.daos.exchangeDAO.updateOrderBooks(message.exchange, message.data);
            break;
        case 'positions':
            bs.daos.exchangeDAO.updatePositions(message.exchange, message.data);
            break;
        case 'signals':
            bs.daos.exchangeDAO.updateSignals(message.exchange, message.data);
            break;
    }
});

router.get('/exchanges/:exchangeId', function(req, res, next) {
    daos.exchangeCollectionDAO.getExchangeById(req.params.exchangeId)
        .then(result => res.status(200).json(result))
        .catch(err => res.status(404).json({'error': `exchange with id ${req.params.exchangeId} not found`}));
});

module.exports = router;
