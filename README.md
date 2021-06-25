## Bitcoin Onion Explorer

The explorer is implemented as an `asyncio` application 
in Python +3.7 with `Quart` and `aiohttp`.

### Testnet btc node

Install Bitcoin Core and run `bitcoind` in testnet mode:

```bash
bitcoind -server -testnet -txindex=0 -prune=0  -rpcuser=bitcoinrpc -rpcpassword=ahything
```

Setup `.cookie` for Bitcoin node RPC:

```bash
echo -n "bitcoinrpc:ahything" > ~/bitcoin/.cookie
```

If you change the above `username:password`, please edit `config.py` 
accordingly.

### Bitcoin blockchain indexer

Build [Blockstream/electrs](https://github.com/Blockstream/electrs):

```bash
sudo apt install clang cmake build-essential 
sudo apt install librocksdb-dev

git clone https://github.com/blockstream/electrs && cd electrs
git checkout new-index

cargo build --locked --release
```

Once built, run with:

```bash
./target/release/electrs -vvv --network testnet --timestamp --http-addr "127.0.0.1:3000"
```

### Bitcoin onion explorer

```
git clone .....
cd ...

pip install -r requirements.txt
```

Run it for development with:
```
env QUART_APP=app quart run
```
or for production with

```
hypercorn app
```