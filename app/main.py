import asyncio

from .utils import isint

from datetime import datetime

from quart import Quart, render_template
from .fetch_blockchain_data import BlockchainFetch

app = Quart(__name__)
app.jinja_options = {}

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


@app.route('/')
async def index():
    async with BlockchainFetch() as fetch:
        recent_blocks = await fetch.recent_blocks(BLOCKS_ON_INDEX)
        btc_chain_status = await fetch.blockchain_info()
        fee_estimate = await fetch.fee_estimate()
        mempool = await fetch.mempool()

    return await render_template(
        "index.html",
        info=(await btc_chain_status.json())['result'],
        recent_blocks=recent_blocks,
        fee_estimate=fee_estimate,
        mempool=mempool)


@app.route('/block/<block_id>')
async def block(block_id):

    print(block_id)

    async with BlockchainFetch() as fetch:

        if len(block_id) == 64:
            a_block = await fetch.block_by_id(block_id)
        else:
            if not isint(block_id):
                app.logger.warning(f'Wrong block_id: {block_id}')
                return await render_template("error.html")

            current_height = await fetch.current_height()
            searched_height = int(block_id)

            if (searched_height > current_height
                    or searched_height < 0):
                app.logger.warning(f'Wrong block_id: {block_id}')
                return await render_template("error.html")

            block_id = await fetch.block_by_height(searched_height)
            a_block = await fetch.block_by_id(block_id)

    return await render_template(
        "block.html",
        block=await a_block.json())


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
