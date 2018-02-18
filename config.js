const path = require('path');
module.exports = {
    botDir: process.env.BOT_DIR || path.join(__dirname, 'bot-engines'),
    pythonPath: 'python3',
    heartBeatInterval: 5000
}
