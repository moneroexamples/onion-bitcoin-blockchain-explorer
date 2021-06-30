import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Esplora Indexer
INDEXER_HOST = '127.0.0.1'
INDEXER_PORT = 3000

# BTC node RPC
BTC_NODE_RPC_HOST = '127.0.0.1'
BTC_NODE_RPC_PORT = 18332
BTC_NODE_RPC_USER = 'bitcoinrpc'
BTC_NODE_RPC_PASSWORD = 'ahything'

BLOCKS_ON_INDEX = 25