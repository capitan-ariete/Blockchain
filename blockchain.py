import os
import logging
import hashlib
import json
from time import time
from urllib.parse import urlparse

if not os.path.isdir('logs'):
    os.makedirs('logs')
if not os.path.isfile('logs/python.log'):
    os.mknod('logs/python.log')

logger = logging.getLogger(__name__)
fileConfig('logger.ini')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# this have to be an environment variable. It's better it becomes https!
protocol_end_point = 'http://'


class BlockChain:

    """
    To know more about blockchain read the following article

    http://www.michaelnielsen.org/ddi/how-the-bitcoin-protocol-actually-works/

    More info about this class within

    https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
    https://github.com/dvf/blockchain/blob/master/blockchain.py

    Warning: Minor changes have been applied to the original class
    """

    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def _valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            logger.debug('Last block: {}'.format(last_block))
            logger.debug('Block: {}'.format(block))

            # Check that the hash of the block is correct
            if block['previous_hash'] != self._hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self._valid_proof(last_block['proof'],
                                    block['proof'],
                                    last_block['previous_hash']):
                return False

            last_block = block
            current_index += 1

        return True

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)

        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in self.nodes:

            # make request and retrieve length and chain
            length, chain = self._make_request(node)

            # if the request failed then continue
            if not length or not chain:
                continue

            # Check if the length is longer and the chain is valid
            if length > max_length and self._valid_chain(chain):
                max_length = length
                new_chain = chain
            else:
                continue

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: <str> The proof given by the Proof of Work algorithm
        :param previous_hash: <str> Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self._hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self._hash(last_block)

        proof = 0
        while self._valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def _hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: <dict> Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def _valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof of work

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """

        guess = '{lp}{p}{lh}'.format(lp=last_proof,
                                     p=proof,
                                     lh=last_hash)

        guess_hash = hashlib.sha256(guess.encode()).hexdigest()

        return guess_hash[:4] == "0000"

    @staticmethod
    def _make_request(node):
        """
        1. Make query to end point
        2. Validate the response status_code

        :param node:
        :return:
        """

        end_point = '{p}{node}/chain'.format(p=protocol_end_point,
                                             node=node)

        response = requests.get(end_point)

        # This part following shall be a separated method
        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']
        else:
            length = None
            chain = None
            logger.error('API response failed with status code: {}'.format(response.status_code))

        return length, chain
