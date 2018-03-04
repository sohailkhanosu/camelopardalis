'use strict';
const EventEmitter = require('events');
const util = require('util');

const PythonShell = jest.fn();

function _fakePythonShell() {
    EventEmitter.call(this);
    this.send = jest.fn();
}

util.inherits(_fakePythonShell, EventEmitter);

module.exports = _fakePythonShell;
