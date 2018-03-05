const botSpawner = require('../botSpawner');
const path = require('path');

jest.mock('fs');
jest.mock('python-shell');
jest.useFakeTimers();

const MARKET_SCRIPTS = ['hitbtc.py', 'exmo.py'];
const scriptToId = {'hitbtc.py': 'hitbtc', 'exmo.py': 'exmo'};

let daos;
let fs;
beforeEach(() => {
    daos = require('../dao')({});
    fs = require('fs');
    fs.__setMarketScripts(MARKET_SCRIPTS);
    require('python-shell').mockReturn
    jest.resetModules();
});

afterEach(() => {
    require('fs').__setMarketScripts([]);
});

it('creates initializes a set of python scripts', () => {
    let bs = botSpawner(null, false, daos);
    MARKET_SCRIPTS.forEach((scriptName) => {
        expect(bs.spawnedChildren.hasOwnProperty(scriptToId[scriptName])).toBe(true);
        let botInstance = bs.spawnedChildren[scriptToId[scriptName]];
        let expectedInstance = {
            id: scriptToId[scriptName],
            running: true,
            scriptPath: scriptName,
            botDir: path.join(process.cwd(), 'bot-engines'),
            fd: expect.objectContaining({'emit': expect.any(Function)}),
        };
        expect(botInstance).toEqual(expectedInstance);
    });
});

it('fails to create scripts if given an incorrect directory through options', () => {
    expect(() => {
        botSpawner({botDir: 'wrongdir'}, false, daos);
    }).toThrow(new Error('no file found'));
});

it('sends out heartbeat messages', () => {
    jest.clearAllTimers()
    // deal with only one market
    let intervalTime = 2000;
    // Given a botSpawner instance with an interval time
    let bs = botSpawner({heartBeatInterval: intervalTime}, false, daos);

    // Then a timeout has been initialized to start heartbeat
    // expect(setTimeout.mock.calls.length).toBe(1);
    expect(setTimeout.mock.calls[0][1]).toEqual(intervalTime);

    // When a certain time period has passed
    jest.runOnlyPendingTimers();

    // The botSpawner sends out a 'ping' message to a given bot
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];
    expect(bot.fd.send.mock.calls.length).toEqual(1);
    expect(bot.fd.send.mock.calls[0][0]).toEqual({type: 'ping', data: 1});
});

it('stops heartbeat messages if bot is determined to be dead', () => {
    jest.clearAllTimers()
    // deal with only one market
    let intervalTime = 2000;
    // Given a botSpawner instance with an interval time
    let bs = botSpawner({heartBeatInterval: intervalTime}, false, daos);

    // Then a timeout has been initialized to start heartbeat
    expect(setTimeout.mock.calls[0][1]).toEqual(intervalTime);

    // When a certain time period has passed
    jest.runOnlyPendingTimers();

    // Then the botSpawner sends out a 'ping' message to a given bot
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];
    expect(bot.fd.send.mock.calls.length).toEqual(1);
    expect(bot.fd.send.mock.calls[0][0]).toEqual({type: 'ping', data: 1});

    // When a pong message has not been received within alotted time
    jest.advanceTimersByTime(5000);

    // Then the bot's running state is turned to false
    expect(bot.running).toBe(false);
});

it('does not send any heartbeat messages to a non-running bot', () => {
    jest.clearAllTimers()
    // deal with only one market
    let intervalTime = 2000;

    // Given a botSpawner instance with an interval time
    let bs = botSpawner({heartBeatInterval: intervalTime}, false, daos);

    // And that has a bot that is turned off
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];
    bot.running = false;

    // Then a timeout has been initialized to start heartbeat
    expect(setTimeout.mock.calls[0][1]).toEqual(intervalTime);

    // When a certain time period has passed
    jest.runOnlyPendingTimers();

    // Then the botSpawner does not send out messages to a bot
    expect(bot.fd.send.mock.calls.length).toEqual(0);
});

it('handles a status type message from a bot', () => {
    // Given a botSpawner instance with at least one bot

    let bs = botSpawner({}, false, daos);
    let mockUpdate = jest.fn();
    daos.exchangeDAO.updateExchange = mockUpdate;
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];
    let expectedStatusMsg = {
        type: 'status',
        exchange: 'hitbtc',
        data: {
            'strategy': 'Basic',
            'markets': {}
        }
    };
    // When a status type message is received
    bot.fd.emit('message', expectedStatusMsg);

    // Then a call to update the exchange is made
    expect(mockUpdate.mock.calls.length).toEqual(1);
    expect(mockUpdate.mock.calls[0]).toEqual([bot.id, expectedStatusMsg.data]);
});

it('handles a balance type message from a bot', () => {
    // Given a botSpawner instance with at least one bot

    let bs = botSpawner({}, false, daos);
    let mockUpdate = jest.fn();
    daos.exchangeDAO.updateBalances = mockUpdate;
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];
    let expectedStatusMsg = {
        type: 'balance',
        exchange: 'hitbtc',
        data: [
            {
                currency: "BTC",
                available: "0.0504600",
                reserved: "0.000000"
            },
            {
                currency: "ETH",
                available: "0.0504600",
                reserved: "0.000000"
            },

        ]
    };
    // When a status type message is received
    bot.fd.emit('message', expectedStatusMsg);

    // Then a call to update the balances is made
    expect(mockUpdate.mock.calls.length).toEqual(1);
    expect(mockUpdate.mock.calls[0]).toEqual([bot.id, expectedStatusMsg.data]);
});

it('handles a active_orders type message from a bot', () => {
    // Given a botSpawner instance with at least one bot

    let bs = botSpawner({}, false, daos);
    let mockUpdate = jest.fn();
    daos.exchangeDAO.updateOrders = mockUpdate;
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];
    let expectedStatusMsg = {
        type: 'active_orders',
        exchange: 'hitbtc',
        data: [
            {
            id: 234242,
            clientOrderId: "cd2342faf",
            symbol: "ETHBTC",
            },
            {
            id: 234243,
            clientOrderId: "cd2342faf",
            symbol: "ETHBTC",
            },
        ]
    };
    // When a status type message is received
    bot.fd.emit('message', expectedStatusMsg);

    // Then a call to update the active_orders is made
    expect(mockUpdate.mock.calls.length).toEqual(1);
    expect(mockUpdate.mock.calls[0]).toEqual([bot.id, expectedStatusMsg.data]);
});

it('saves the current running state of a bot', () => {
    daos.exchangeCollectionDAO.addExchange = jest.fn();
    daos.exchangeDAO.updateExchangeRunningState = jest.fn();

    // Given a botspawner instance
    // When it is initialized
    let bs = botSpawner({}, false, daos);
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];

    // Then state information is saved
    expect(daos.exchangeCollectionDAO.addExchange.mock.calls.length).toEqual(2);
    expect(daos.exchangeCollectionDAO.addExchange.mock.calls[0][0]).toEqual(bot.id);
    expect(daos.exchangeDAO.updateExchangeRunningState.mock.calls.length)
        .toEqual(2);
    expect(daos.exchangeDAO.updateExchangeRunningState.mock.calls[0])
        .toEqual([bot.id, true]);
});

it('can stop a bot', () => {
    // Given a botspawner instance
    let bs = botSpawner({}, false, daos);
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];
    let mockUpdate = jest.fn();

    // When it is signalled to be stopped
    daos.exchangeDAO.updateExchangeRunningState = mockUpdate;
    bs.stopBot(bot.id);

    // Then a message is sent to it for shutdown
    expect(bot.fd.send.mock.calls[0][0]).toEqual({type: 'shutdown'});

    // And its running state is set to false
    expect(bot.running).toBe(false);

    // And this information is persisted
    expect(mockUpdate.mock.calls.length).toEqual(1);
});

it('can start a bot', () => {
    // Given a botspawner instance that has a bot that is stopped
    let bs = botSpawner({}, false, daos);
    let bot = bs.spawnedChildren[Object.keys(bs.spawnedChildren)[0]];
    let mockUpdate = jest.fn();
    bot.running = false;


    // When it is signalled to be started
    daos.exchangeDAO.updateExchangeRunningState = mockUpdate;
    daos.exchangeCollectionDAO.addExchange = jest.fn(()=> new Promise((res, rej)=>res()));
    bs.startBot(bot.id);

    // Then its running state is switched on
    expect(bs.spawnedChildren[bot.id].running).toBe(true);

    // And this information is persisted
    expect(mockUpdate.mock.calls.length).toEqual(1);
});
