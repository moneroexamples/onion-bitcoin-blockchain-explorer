import asyncio
import logging

import aiohttp



class BlockchainFetch:

    indexer_protocol = 'http'
    indexer_host = '127.0.0.1'
    indexer_port = 3000

    node_protocol = 'http'
    node_host = '127.0.0.1'
    node_port = 18332
    node_rpcuser = ''
    node_rpcpassword = ''

    def __init__(self):
        self._indexer_url = f"{BlockchainFetch.indexer_protocol}://{BlockchainFetch.indexer_host}:{BlockchainFetch.indexer_port}"
        self._node_url = (f"{BlockchainFetch.node_protocol}://{BlockchainFetch.node_rpcuser}:{BlockchainFetch.node_rpcpassword}"
                          + f"@{BlockchainFetch.node_host}:{BlockchainFetch.node_port}")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logging.error(str(exc_val))

        await self.session.close()
        return True

    async def _get(self, url):
        return await self.session.get(
            f'{self._indexer_url}{url}')

    async def _node_post(self, payload):
        payload.update({"jsonrpc": "1.0", "id": "curltext"})
        return await self.session.post(
            self._node_url, json=payload)

    async def current_height(self):
        return int(await (await self._get(
            '/blocks/tip/height')).text())

    async def fee_estimate(self):
        return await (await self._get(
            '/fee-estimates')).json()

    async def mempool(self):
        return await (await self._get(
            '/mempool')).json()

    async def __recent_blocks(self,
                            start_height=None):
        if not start_height:
            return await self._get('/blocks')
        else:
            return await self._get(
                f'/blocks/{start_height}')

    async def recent_blocks(self,
                            blocks_count=None):
        if not blocks_count:
            result = await self.__recent_blocks()
        else:
            current_height = await self.current_height()

            result = await asyncio.gather(
                *[self.__recent_blocks(start_height)
                  for start_height in range(current_height,
                                            current_height - blocks_count,
                                            -10)]
            )

        recent_blocks = []

        for blocks in result:
            recent_blocks += await blocks.json()

        return recent_blocks

    async def blockchain_info(self):
        payload = {"method": "getblockchaininfo",
                   "params": []}
        return await self._node_post(payload)

    async def block_by_id(self, block_id):
        return await self._get(f'/block/{block_id}')

    async def block_by_height(self, block_height):
        return await(await self._get(f'/block-height/{block_height}')).text()

    async def all_block_txs_ids(self, block_id):
        return await self._get(f'/block/{block_id}/txids')

    async def tx_outspends(self, tx_id):
        return await self._get(f'/tx/{tx_id}/outspends')

    async def tx_status(self, tx_id):
        return await self._get(f'/tx/{tx_id}')

    async def block_txs(self, block_id):

        block_txs_ids = await(
            await self.all_block_txs_ids(block_id)).json()

        results = await asyncio.gather(
            *[self.tx_status(tx_id) for tx_id in block_txs_ids]
        )

        block_txs = await asyncio.gather(
            *[result.json() for result in results]
        )

        # add total transfer value
        for tx in block_txs:
            vin_total = sum([vi.get("value", 0) for vi in tx.get("vin", [])])
            vout_total = sum([vo.get("value", 0) for vo in tx.get("vout", [])])
            #print(tx['txid'], vin_total, vout_total, [vi.get("vout", 0) for vi in tx.get("vin", [])])
            tx["total_value"] = vout_total - vin_total

        return block_txs


