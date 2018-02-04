const PythonShell = require('python-shell');
const config = require('./config');
const util = require('util');
const EventEmitter = require('events');
const fs = require('fs');
const path = require('path');


function getIdFromScriptPath(scriptPath) {
    return path.parse(scriptPath).name;
}

function initBot(spawner, botDirectory, scriptPath) {
    var options = {
        mode: 'json',
        pythonPath: config.pythonPath,
        scriptPath: botDirectory
    }

    var botInstance = {
        running: false,
        scriptPath: scriptPath,
        fd: null
    };
    botInstance.fd = new PythonShell(scriptPath, options);
    botInstance.fd.on('message', function (message) {
        spawner.emit('message', message);
    });
    botInstance.running = true;
    spawner.spawnedChildren[getIdFromScriptPath(scriptPath)] = botInstance;
}

/**
 * given a set of options, if any, configures/runs the bots in the specified
 * directory (given in config.js or provided in options as botDir)
 * this provides an event emitter interface, so clients can listen on messages
 * and receive an instance of data from any of the instantiated bots
 *
 * to send data to a specific bot instance, use the method send with parameters bot_id and data
 *
 * to stop a script use the instance method stopBot and provide the bot_id
 *
 * to start a script use the instance method startbot and provide the bot_id
 *
 * to restart a script use the instance method restartBot and provide the bot_id
 */
function BotSpawner(options) {
    EventEmitter.call(this);

    options = options || {};
    const self = this;
    let botDir = options.botDir || config.botDir;
    this.spawnedChildren = {};  // Object[Text, Object]

    fs.readdir(botDir, function(err, files) {
        files
            .filter(fname => fname.endsWith('.py'))
            .forEach(fname => {
                initBot(self, botDir, fname);
        })
    });

    this.stopBot = function(botId) {
        // stop the bot, send a signal to it or send EOF
    }

    this.startBot = function(botId) {
        // start the bot, (if started, ignore)
    }

    this.restartBot = function(botId) {
        // restart the bot
        this.stopBot(botId);
        this.startBot(botId);
    }
}

util.inherits(BotSpawner, EventEmitter);
module.exports = BotSpawner;
