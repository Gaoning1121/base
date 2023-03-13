from eth_keys import keys
from eth_utils import decode_hex
import os

n = 50  # 生成的钱包数
wallet_file = "wallet2.txt"
wallets = []

for i in range(n):
    private_key = keys.PrivateKey(os.urandom(32))
    public_key = private_key.public_key
    address = keys.PublicKey(public_key.to_bytes()).to_checksum_address()
    wallets.append([address,private_key.to_hex()])
  
with open(wallet_file, mode='w') as file:
    for wallet in wallets:
        file.write(wallet[0] + "," + wallet[1] + "\n")
