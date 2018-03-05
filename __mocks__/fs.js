'use strict';

const path = require('path');

const fs = jest.genMockFromModule('fs');

let testMarketScripts = {scripts: []};

function __setMarketScripts(marketScripts) {
    testMarketScripts.scripts = marketScripts;
}
function readdir(name, callback) {
    if (name === path.join(process.cwd(), 'bot-engines'))
        return callback(null, testMarketScripts.scripts);
    return callback(new Error('no file found'), null);
}

fs.readdir = readdir;
fs.__setMarketScripts = __setMarketScripts;

module.exports = fs;
