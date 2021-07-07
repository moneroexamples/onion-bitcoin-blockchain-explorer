import asyncio
import logging
import random

from .utils.utils import isint

from datetime import datetime

from quart import Quart, render_template, request, redirect

from .fetch_blockchain_data import BlockchainFetch

app = Quart(__name__)

app.jinja_options = {}

app.logger.level = logging.INFO

# load config.py
app.config.from_object('config')

# setup BlockchainFetch
BlockchainFetch.indexer_host = app.config['INDEXER_HOST']
BlockchainFetch.indexer_port = app.config['INDEXER_PORT']

BlockchainFetch.node_host = app.config['BTC_NODE_RPC_HOST']
BlockchainFetch.node_port = app.config['BTC_NODE_RPC_PORT']
BlockchainFetch.node_rpcuser = app.config['BTC_NODE_RPC_USER']
BlockchainFetch.node_rpcpassword = app.config['BTC_NODE_RPC_PASSWORD']

BLOCKS_ON_INDEX = app.config['BLOCKS_ON_INDEX']

fetch = BlockchainFetch()


@app.before_serving
async def init():
    app.logger.info("Initializing BlockchainFetch")
    await fetch.init()


async def update_block_list():
    '''
    This runs periodically in the event loop
    to keep the list of the most recent blocks
    up to date in our lru cache

    :return: None
    '''

    while True:
        app.logger.info("Refreshing block cache")

        recent_blocks = await fetch.recent_blocks(BLOCKS_ON_INDEX)

        # just start tx block scans. we do not await for the results as
        # we do not need them here. This is just so that we start
        # populating our block cache
        #[asyncio.create_task(fetch.block_txs(block['id']))
        #    for block in recent_blocks]
        asyncio.gather(
            *[fetch.block_txs(block['id']) for block in recent_blocks]
        )

        # sleep from some time before next refresh
        # add some random time so that if you run it in multiple
        # workers, they don't hit our indexer at the same time
        await asyncio.sleep(120 + random.randint(-20, 20))


async def get_current_mempool_txs():
    '''
    This runs periodically in the event loop
    to keep the list of the most recent blocks
    up to date in our lru cache

    :return: None
    '''

    while True:
        app.logger.info("Getting mempool txs")

        mempool_txs = await fetch.mempool_txs_from_node(True)

        print(await mempool_txs.json())

        # sleep from some time before next refresh
        # add some random time so that if you run it in multiple
        # workers, they don't hit our indexer at the same time
        await asyncio.sleep(110 + random.randint(-2, 2))


@app.before_serving
async def run_loop():
    current_loop = asyncio.get_running_loop()
    asyncio.ensure_future(update_block_list(), loop=current_loop)
    asyncio.ensure_future(get_current_mempool_txs(), loop=current_loop)


@app.after_serving
async def close():
    await fetch.close()


@app.route('/')
async def index():

    recent_blocks = await fetch.recent_blocks(BLOCKS_ON_INDEX)

    txs_in_blocks_fut = asyncio.gather(
        *[fetch.block_txs(block['id']) for block in recent_blocks]
    )

    btc_chain_status = await fetch.blockchain_info()

    mempool_recent_task = asyncio.create_task(fetch.mempool_recent())

    fee_estimate = await fetch.fee_estimate()
    mempool = await fetch.mempool()
    #mempool_txids = await fetch.mempool_txids()

    #print(await mempool_txids.json())

    # mempool_from_node = await fetch.mempool_txs_from_node(True)
    # print(await mempool_from_node.text())

    chain_tx_stats = await fetch.chain_tx_stats()

    if not recent_blocks:
        return await render_template(
            "error.html")

    txs_in_blocks = await txs_in_blocks_fut

    mempool_recent = await mempool_recent_task

    # TODO: eliminate this loop
    for block, txs in zip(recent_blocks, txs_in_blocks):
        block.update(txs)

    return await render_template(
        "index.html",
        info=(await btc_chain_status.json())['result'],
        recent_blocks=recent_blocks,
        fee_estimate=fee_estimate,
        mempool_recent=await mempool_recent.json(),
        txs_stats=(await chain_tx_stats.json())['result'],
        mempool=mempool)


@app.route('/block/<block_id>')
async def block(block_id):

    if len(block_id) == 64:
        a_block = await fetch.block_by_id(block_id)
    else:
        if not isint(block_id):
            app.logger.warning(f"Wrong block_id: {block_id}")
            return await render_template(
                "error.html",
                msg=f"Wrong block_id: {block_id}")

        current_height = await fetch.current_height()
        searched_height = int(block_id)

        if (searched_height > current_height
                or searched_height < 0):
            app.logger.warning(f'Wrong block_id: {block_id}')
            return await render_template(
                "error.html",
                msg=f"Wrong block_id: {block_id}")

        block_id = await fetch.block_by_height(searched_height)
        a_block = await fetch.block_by_id(block_id)

    block_txs = await fetch.block_txs(block_id)

    return await render_template(
        "block.html",
        block=await a_block.json(),
        block_txs=block_txs)


@app.route('/tx/<tx_id>')
async def tx(tx_id):

    if len(tx_id) != 64:
        return await render_template(
            "error.html",
            msg=f"Wrong tx_id: {tx_id}")

    tx_status = await fetch.tx_status(tx_id)

    if tx_status.status != 200:
        return await render_template(
            "error.html",
            msg=f"Transaction {tx_id} not found")

    return await render_template(
        "transaction.html",
        tx=await tx_status.json())


@app.route('/address/<address>')
async def address(address):

    if len(address) not in [34, 35, 42]:
        return await render_template(
            "error.html",
            msg=f"Wrong address: {address}")

    address_txs_task = asyncio.create_task(
        fetch.address_txs(address))

    address_info = await fetch.address(address)

    if address_info.status != 200:
        return await render_template(
            "error.html",
            msg=f"Invalid or not found {address}")

    address_txs = await address_txs_task

    return await render_template(
        "address.html",
        address=await address_info.json(),
        txs=await address_txs.json())

@app.route('/search')
async def search():

    value = request.args.get('value', None)

    if not value:
        return await render_template(
            "error.html",
            msg=f"No search value provided")

    value = value.strip()

    # first check if we search for an address
    address_info = await fetch.address(value)

    if address_info.status == 200:
        return redirect(f'/address/{value}')

    # next check if we search for a transaction
    tx_status = await fetch.tx_status(value)

    if tx_status.status == 200:
        return redirect(f'/tx/{value}')

    # finally check for block
    a_block = await fetch.block_by_id(value)

    if a_block.status == 200:
        return redirect(f'/block/{value}')

    block_id = await fetch.block_by_height(value)

    if "not found" not in block_id:
        return redirect(f'/block/{block_id}')

    return await render_template(
        "error.html",
        msg=f"Can't find {value}")


@app.template_filter()
def timedelta(timestamp):
    delta = datetime.now() - datetime.fromtimestamp(int(timestamp))
    minutes_count = round(delta.seconds / 60)

    if minutes_count < 60:
        return f"00:{minutes_count:02.0f}"
    else:
        hours_count = delta.seconds // 3600
        left_minutes = (delta.seconds % 3600) / 60
        return f"{hours_count:02.0f}:{left_minutes:02.0f}"


import werkzeug.exceptions


@app.errorhandler(werkzeug.exceptions.NotFound)
async def handle_not_found(e):
    return await render_template("error.html"), 404


@app.errorhandler(Exception)
async def server_error(err):
    app.logger.error(str(err))
    return await render_template('error.html'), 500