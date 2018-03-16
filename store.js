const fs = require('fs');
const path = require('path');
const config = require('./config');
const {promisify} = require('util');
const Storage = require('@google-cloud/storage');
const storage = new Storage({projectId: 'camelopardalis-467-1'});
const bucketName = 'camelopardalis-467-1-dumps'


function uploadFileToGCS(filename) {
    return storage.bucket(bucketName)
        .upload(filename)
        .catch(err => console.log(`GCS ERROR: unable to upload ${filename}`));
}

function downloadFileFromGCS(filename, destination) {
    let options = {destination};

    return storage.bucket(bucketName)
        .file(filename)
        .download(options)
        .catch(err => console.log('GCS ERROR: ', err.message || err));
}


function getObjectToDump(store) {
    let dataToDump = {};
    Object.keys(store).forEach(key=> {
        if (key[0] === '_')
            return;
        dataToDump[key] = store[key];
    });
    return dataToDump;
}


class ObjectStore {
    constructor() {

        /* try loading from google cloud storage */
        let startPromise;
        if (config.useCloudStorage) {
            startPromise = downloadFileFromGCS(config.dumpFile, path.join(__dirname, config.dumpFile));
        } else {
            startPromise = Promise.resolve();
        }

        /* load the data file if it exists, else just return */
        startPromise.then(() => promisify(fs.readFile)(config.dumpFile, 'utf-8'))
            .then(contents=> Object.assign(this, JSON.parse(contents)))
            .catch(err => console.log('no dump file found, it will be created now'))
            .then(() => {
                /* then setup regular file backups at specified interval */
                this._dumpLoop = setInterval(() => {
                    let objectToDump = getObjectToDump(this);
                    promisify(fs.writeFile)(config.dumpFile, JSON.stringify(objectToDump), 'utf-8')
                        .catch(err => 'unable to write to ' + config.dumpFile)
                        .then(() => {
                            /* try to save to google cloud */
                            if (config.useCloudStorage) {
                                uploadFileToGCS(config.dumpFile);
                            }
                        });
                }, config.dumpInterval);
            });
    }
}

let store = new ObjectStore();

module.exports = store;
