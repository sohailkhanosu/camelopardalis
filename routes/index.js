const express = require('express');
const router = express.Router();
const store = require('../store');
const dao = require('../dao')(store);
const bs = require('../botSpawner')();

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Express' });
});

router.get('/state', function(req, res, next) {
    dao.exchangeCollectionDAO.getStatus()
        .then((data) => res.json(data));
})

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
    dao.exchangeCollectionDAO.getStatus()
        .then((data) => res.json(data));
})

router.get('/exchanges/:exchangeId', function(req, res, next) {
    dao.getExchangeById(req.params.exchangeId)
        .then(result => res.status(200).json(result))
        .catch(err => res.status(404).json({'error': `exchange with id ${req.params.exchangeId} not found`}));
})

module.exports = router;
