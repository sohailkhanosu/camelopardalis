const daoCreator = require('../dao');

describe('exchange collection (collection of exchanges)', () => {
    beforeEach(() => {
        this.exchangeCollectionDAO = daoCreator({}).exchangeCollectionDAO;
    });

    afterEach(() => {
        delete this.exchangeCollectionDAO;
    });

    it('initializes a new exchange', () => {
        expect.assertions(1);
        return expect(this.exchangeCollectionDAO.addExchange('tester')).resolves.toEqual({});
    });

    it('rejects adding a duplicate exchange', () => {
        expect.assertions(1);
        return expect(this.exchangeCollectionDAO.addExchange('tester')
            .then(() => this.exchangeCollectionDAO.addExchange('tester')))
            .rejects.toEqual('already added exchange: tester');
    });

    it('returns the status for all exchanges', () => {
        /* add some exchanges */
        let expectedResult = {
            data: {
                tester: {
                    strategy: 'test',
                    running: true,
                    balances: [],
                    activeOrders: [],
                    trades: [],
                    orderBooks: [],
                    markets: {}
                }
            },
            'type': 'status-all'
        }
        expect.assertions(1);

        /* manually replace the store data */
        this.exchangeCollectionDAO.store.tester = expectedResult.data.tester;

        /* and then try to obtain it */
        return this.exchangeCollectionDAO.getStatus().then(rv => {
            expect(rv).toEqual(expectedResult);
        });
    })
});
