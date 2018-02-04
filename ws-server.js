const WebSocket = require('ws');
const BotSpawner = require('./botSpawner.js');
const bs = new BotSpawner();

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
}

module.exports = function registerWSS(server) {
    const wss = new WebSocket.Server({ server });
    wss.on('connection', clientHandler);
};
