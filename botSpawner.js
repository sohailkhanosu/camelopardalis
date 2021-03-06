const PythonShell = require('python-shell');
const config = require('./config');
const util = require('util');
const EventEmitter = require('events');
const fs = require('fs');
const path = require('path');


function getIdFromScriptPath(scriptPath) {
    return path.parse(scriptPath).name;
}


/* start a heartbeat check with the given botInstance at every intervalTime seconds */
function startHeartBeat(botInstance, intervalTime, daos) {
    let counter = 1;
    let intervals = [];
    setTimeout(function checker() {
        let currentCounter = counter;
        let pongReceived = false;
        if (botInstance.running) {
            try {
                botInstance.fd.send({type: 'ping', data: currentCounter});
            } catch(err) {
                /* assume the worst, client closed connection */
                botInstance.running = false;
                daos.exchangeDAO.updateExchangeRunningState(botInstance.id, false);
                return;
            }
            botInstance.fd.once(`${botInstance.id}-pong`, function pongListener(message) {
                if (message.type === 'pong' && message.data >= currentCounter) {
                    pongReceived = true;
                } else {
                    botInstance.fd.once(`${botInstance.id}-pong`, pongListener);
                }
            });

            setTimeout(function () {
               if (!pongReceived) {
                   /* consider this bot dead */
                   botInstance.running = false;
                   daos.exchangeDAO.updateExchangeRunningState(botInstance.id, false);
               } else {
                   /* got the pong, restart the checker */
                   setTimeout(checker, intervalTime);
               }
            }, 5000);
        }
        counter += 1;
    }, intervalTime)
}

/* initialize the bot script to run */
function initBot(spawner, botDirectory, scriptPath) {
    let options = {
        mode: 'json',
        pythonPath: config.pythonPath,
        scriptPath: botDirectory
    }

    let botInstance = {
        running: false,
        scriptPath: scriptPath,
        botDir: botDirectory,
        fd: null,
        id: getIdFromScriptPath(scriptPath)
    };
    botInstance.fd = new PythonShell(scriptPath, options);
    botInstance.fd.on('message', function (message) {
        /* do not propagate private types such as ping/pong */
        if (message.type !== 'pong')
            spawner.emit('message', message);
        else {
            botInstance.fd.emit(`${botInstance.id}-pong`, message)
        }

    });
    botInstance.fd.on('error', function (message) {
        console.error('stream error', message);
    });

    botInstance.running = true;
    spawner.spawnedChildren[botInstance.id] = botInstance;

    /* start the heartbeat to ensure continuous connection */
    startHeartBeat(botInstance, spawner.heartBeatInterval, spawner.daos);

    /* register the exchange data, if its not found */
    spawner.daos.exchangeDAO.findExchangeById(botInstance.id)
        .catch(() => spawner.daos.exchangeCollectionDAO.addExchange(botInstance.id))
        .then(() => spawner.daos.exchangeDAO.updateExchangeRunningState(botInstance.id, botInstance.running));
}


/**
 * given a set of options, if any, configures/runs the bots in the specified
 * directory (given in config.js or provided in options as botDir)
 * this provides an event emitter interface, so clients can listen on messages
 * and receive an instance of data from any of the instantiated bots
 *
 * daos are a set of data access objects used to manipulate state across app
 *
 * to send data to a specific bot instance, use the method send with parameters bot_id and data
 *
 * to stop a script use the instance method stopBot and provide the bot_id
 *
 * to start a script use the instance method startbot and provide the bot_id
 *
 * to restart a script use the instance method restartBot and provide the bot_id
 */
function BotSpawner(options, daos) {
    EventEmitter.call(this);

    this.daos = daos;
    options = options || {};
    const self = this;
    let botDir = options.botDir || config.botDir;
    this.spawnedChildren = {};  // Object[Text, Object]
    this.heartBeatInterval = options.heartBeatInterval || 2000; // by default, wait two seconds to send heartbeat

    fs.readdir(botDir, function(err, files) {
        if (err) {
            throw err;
        }
        files
            .filter(fname => fname.endsWith('.py'))
            .forEach(fname => {
                initBot(self, botDir, fname);
        })
    });

    this.stopBot = function(botId) {
        // stop the bot, send a signal to it or send EOF
        if (this.spawnedChildren.hasOwnProperty(botId) && this.spawnedChildren[botId].running) {
            this.spawnedChildren[botId].fd.send({'type': 'shutdown'});
            // maybe listen here for a message of type shutdown-confirm that has
            // the same botId
            this.spawnedChildren[botId].running = false;
            this.daos.exchangeDAO.updateExchangeRunningState(botId, false);
        }
    }

    this.startBot = function(botId) {
        // start the bot, (if started, ignore)
        if (this.spawnedChildren.hasOwnProperty(botId) && !this.spawnedChildren[botId].running) {
            // check to see if the process is not running and is terminated
            // it could have been signaled for shutdown but not yet have exited
            /* in this case, lets just delete the original instance and start a new one */
            var script = this.spawnedChildren[botId].scriptPath;
            var botDir = this.spawnedChildren[botId].botDir;
            delete this.spawnedChildren[botId];
            initBot(self, botDir, script);
        }
    }

    this.restartBot = function(botId) {
        this.stopBot(botId);

        /* start bot after a two second delay to ensure termination */
        setTimeout(() => this.startBot(botId), 2000);
    }
}

util.inherits(BotSpawner, EventEmitter);

var _bs = null;

/*
 * daos is an object that contains initialized instances of data access objects
 */
module.exports = function (config, use_singleton, daos) {
    /* use singleton by default, otherwise, for testing, construct new obj  */
    use_singleton = use_singleton === undefined ? true: use_singleton;
    if (use_singleton) {
        if (_bs === null) {
            _bs = new BotSpawner(config || {}, daos);
        }
        return _bs;
    } else {
        return new BotSpawner(config || {}, daos);
    }
}
