import asyncio

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
        await self.session.close()

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





