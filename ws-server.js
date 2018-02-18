const WebSocket = require('ws');
const bs = require('./botSpawner.js')();
const store = require('./store');
const ecDAO = require('./dao')(store).exchangeCollectionDAO;

function clientHandler(ws, req) {
    function messageForwarder(message) {
        try {
            ws.send(JSON.stringify(message));
        } catch (err) {
            console.log('unknown error detected');
        }
        
    }
    ws.on('close', function () {
        console.log('client closed connelction');
        bs.removeListener('message', messageForwarder);
        ws.close();
    });
    ws.on('error', function () {
        console.log('error detected');
        bs.removeListener('message', messageForwarder);
        ws.close();
    })

    bs.on('message', messageForwarder);

    /* forward the initial state to the client */
    ecDAO.getStatus().then((data) => ws.send(JSON.stringify(data)));
}

module.exports = function registerWSS(server) {
    const wss = new WebSocket.Server({ server });
    wss.on('connection', clientHandler);
};
