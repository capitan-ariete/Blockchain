import os
import logging.config
from logging.config import fileConfig
from uuid import uuid4
from flask import Flask, jsonify, request
import blockchain
from argparse import ArgumentParser

if not os.path.isdir('logs'):
    os.makedirs('logs')
if not os.path.isfile('logs/python.log'):
    os.mknod('logs/python.log')

logger = logging.getLogger(__name__)
fileConfig('logger.ini')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
bk = blockchain.BlockChain()

"""
To know more about flask:
https://scotch.io/tutorials/build-a-restful-api-with-flask-the-tdd-way
"""


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = bk.last_block
    proof = bk.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    bk.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = bk.hash(last_block)
    block = bk.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        message = 'Missing values'
        return message, 400

    # Create a new Transaction
    index = bk.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': bk.chain,
        'length': len(bk.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')

    if nodes is None:
        message = "Please supply a valid list of nodes"
        return message, 400

    for node in nodes:
        bk.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(bk.nodes),
    }

    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = bk.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': bk.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': bk.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    logger.info("IT'S SHOWTIME")

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='Port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
