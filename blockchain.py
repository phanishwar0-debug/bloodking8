import hashlib
import json
import time
from datetime import datetime
from typing import List, Dict, Any

class Block:
    def __init__(self, index: int, timestamp: str, data: Dict[str, Any], previous_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = [self.create_genesis_block()]
        
    def create_genesis_block(self) -> Block:
        return Block(0, str(datetime.now()), {"message": "Genesis Block", "type": "genesis"}, "0")
    
    def get_latest_block(self) -> Block:
        return self.chain[-1]
    
    def add_block(self, data: Dict[str, Any]) -> str:
        latest_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=str(datetime.now()),
            data=data,
            previous_hash=latest_block.hash
        )
        self.chain.append(new_block)
        return new_block.hash
    
    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_block_by_hash(self, block_hash: str) -> Block:
        for block in self.chain:
            if block.hash == block_hash:
                return block
        return None
    
    def get_all_blocks(self) -> List[Dict[str, Any]]:
        return [block.to_dict() for block in self.chain]
    
    def get_chain_length(self) -> int:
        return len(self.chain)

# Global blockchain instance
blood_donation_blockchain = Blockchain()