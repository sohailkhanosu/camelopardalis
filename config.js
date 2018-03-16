const path = require('path');
module.exports = {
    botDir: process.env.BOT_DIR || path.join(__dirname, 'bot-engines'),
    pythonPath: 'python3',
    heartBeatInterval: 5000,
    dumpFile: 'state-dump.json',
    dumpInterval: 60 * 1000,     /* in milliseconds */
    useCloudStorage: false        /* enable fetch/store from cloud storage */
}
