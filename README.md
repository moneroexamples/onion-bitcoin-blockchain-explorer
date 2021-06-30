## Bitcoin Onion Explorer 

The explorer is implemented as an `asyncio` application 
in Python +3.7 with `Quart` and `aiohttp`.

### TO DO

Still lots of things to do, as this is the **very early stage** of the development. But 
issues, comments and testing is already being welcomed. 

### Testnet btc node

Install Bitcoin Core and run `bitcoind` in the testnet mode with some rpcuser and rpcpassword
which are set here as `bitcoinrpc` and `secretpassword222` as examples:

```bash
bitcoind -server -testnet -txindex=0 -prune=0 -rpcuser=bitcoinrpc -rpcpassword=secretpassword222
```

Setup `.cookie` for Bitcoin node RPC:

```bash
echo -n "bitcoinrpc:secretpassword222" > ~/bitcoin/testnet3/.cookie
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

### Onion Bitcoin blockchain explorer

```
git clone https://github.com/moneroexamples/onion-bitcoin-blockchain-explorer.git
cd onion-bitcoin-blockchain-explorer

sudo apt install python3-pip python3-venv 
python -m venv venv
source ./venv/bin/activate

pip3 install pip --upgrade

pip install -r requirements.txt
```

Run it for development with:
```
env QUART_APP=app quart run
```
or for production with 2 workers:

```
hypercorn app -w 2
```

## Other monero examples

Other examples can be found on  [github](https://github.com/moneroexamples?tab=repositories).
Please know that some of the examples/repositories are not
finished and may not work as intended.

## How can you help?

Constructive criticism, code and website edits are always good. They can be made through Github.