import web3
from web3 import Web3
import requests
import concurrent.futures
import random
import time


class Rpc:
    def __init__(self, rpc='https://goerli.base.org', chainid=84531, proxies=None, timeout=30):
        self.rpc = rpc
        self.chainid = chainid
        self.proxies = proxies
        self.timeout = timeout
        self.eth = Web3(Web3.HTTPProvider(self.rpc)).eth

    def get_gas_price(self):
        data = {"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}
        res = self._post_request(data)
        return res.json()

    def get_transaction_count_by_address(self, address):
        data = {"jsonrpc":"2.0","method":"eth_getTransactionCount","params":[address,'latest'],"id":1}
        res = self._post_request(data)
        return res.json()

    def send_raw_transaction(self, hex):
        data = {"jsonrpc":"2.0","method":"eth_sendRawTransaction","params":[hex],"id":1}
        res = self._post_request(data)
        return res.json()

    def transfer(self, account, to, amount, gaslimit, **kw):
        amount = int(amount, 16) if isinstance(amount, str) else int(amount)
        gaslimit = int(gaslimit, 16) if not isinstance(gaslimit, int) else gaslimit
        gasprice = int(self.get_gas_price()['result'], 16)
        nonce = int(self.get_transaction_count_by_address(account.address)['result'], 16)
        tx = {'from': account.address, 'value': amount,'to': to, 'gas': gaslimit, 'gasPrice': gasprice, 'nonce': nonce, 'chainId': self.chainid}
        if kw:
            tx.update(**kw)
        signed = account.signTransaction(tx)
        return self.send_raw_transaction(signed.rawTransaction.hex())

    def _post_request(self, data):
        headers = {
            'content-type': 'application/json',
            'accept-encoding': 'gzip, deflate, br',
            'user-agent': self._generate_user_agent(),
        }
        res = requests.post(self.rpc, json=data, headers=headers, proxies=self.proxies, timeout=self.timeout)
        return res

    def _generate_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        ]
        return random.choice(user_agents)

def run_task(task, account, rpc):
    retry = 0
    while retry < 5:
        try:
            res = rpc.transfer(account, to=task['to'], amount=task['amount'], gaslimit=task['gaslimit'], data=task['data'])
            return res  
        except Exception as e:
            print(f'交易失败: {account.address} -> {task["to"]}, 错误信息: {e}')
            retry += 1

            if retry == 5:
                print(f'任务 {task["to"]} 尝试 {retry} 次后失败')

def execute_tasks(task_list, account_list, rpc):
    tx_hashes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(run_task, task, account, rpc): (task, account) for task, account in zip(task_list, account_list)}
        for future in concurrent.futures.as_completed(futures):
            task, account = futures[future]
            try:
                tx_hash = future.result()
                if tx_hash:
                    #print(f'交易成功: {account.address} -> {task["to"]}, 交易哈希： {tx_hash}')
                    tx_hashes.append(tx_hash)
                else:
                    print(f'交易失败: {account.address} -> {task["to"]}, 交易哈希: {tx_hash}, 未收到交易哈希')
            except Exception as e:
                print(f'运行任务失败: {account.address} -> {task["to"]}, 错误信息: {e}')
                if retry == 5:
                    print(f'交易失败: {account.address} -> {task["to"]}, 没有更多的重试次数，错误信息: {e}')
                    continue

            try:
                tx_hash_str = future.result()
                tx_hash_str = tx_hash_str['result']
                tx_hash_bytes = tx_hash_str
                receipt = rpc.eth.waitForTransactionReceipt(tx_hash_bytes)
                #print(f'交易确认: {tx_hash}, 序号 {receipt["blockNumber"]}')
            except TypeError as e:
                print(f'无法获取交易信息，错误信息: {e}')
            
    return tx_hashes

if __name__ == '__main__':
    with open('wallet.txt', 'r') as f:
        privkeys = f.readlines()
    with open('wallet2.txt', 'r') as f:
        accounts = f.readlines()
    assert len(privkeys) == len(accounts), "The number of accounts must be equal in wallet.txt and wallet2.txt."
    
    rpc = Rpc(rpc='https://goerli.base.org', chainid=84531)

    for i in range(len(privkeys)):
        account = web3.Account.from_key(privkeys[i][:-1].split(',')[0])

        # 任务1 Claim
        data1 = '0xbe895ece'
        task_1 = {'to': '0xDDB6DcCE6B794415145Eb5cAa6CD335AEdA9C272', 'amount': 0, 'gaslimit': 280000, 'data': data1}
        print(f"第{i+1}个任务: 执行Claim...")
        tx_hashes_1 = execute_tasks([task_1], [account], rpc)
        # 等待第一个任务完成
        tx_hash = tx_hashes_1[0]['result']
        receipt = rpc.eth.waitForTransactionReceipt(tx_hash)
        if receipt.status == 1:
            print(f"第{i+1}个任务: Claim已完成！")
        else:
            print(f"第{i+1}个任务: Claim失败, 已经有猫了！")

        # 任务2 Transfer
        recipient_address = accounts[i][:-1].split(',')[0]
        data2 = '0xf242432a' + account.address[2:].rjust(64,'0') + recipient_address[2:].rjust(64,'0') + '0000000000000000000000000000000000000000000000000000000000000000' + '0000000000000000000000000000000000000000000000000000000000000001' + '00000000000000000000000000000000000000000000000000000000000000a0' + '0000000000000000000000000000000000000000000000000000000000000001' + '0000000000000000000000000000000000000000000000000000000000000000'
        task_2 = {'to': '0xDDB6DcCE6B794415145Eb5cAa6CD335AEdA9C272', 'amount': 0, 'gaslimit': 280000, 'data': data2}
        print(f"第{i+1}个任务: 执行Transfer...")
        tx_hashes_2 = execute_tasks([task_2], [account], rpc)
        # 等待第二个任务完成
        tx_hash = tx_hashes_2[0]['result']
        receipt = rpc.eth.waitForTransactionReceipt(tx_hash)
        if receipt.status == 1:
            print(f"第{i+1}个任务: Transfer已完成！")
        else:
            print(f"第{i+1}个任务: Transfer失败！")
        
        # 任务3 Burn
        data3 = '0xf5298aca' + account.address[2:].rjust(64,'0') + '0000000000000000000000000000000000000000000000000000000000000001' + '0000000000000000000000000000000000000000000000000000000000000001'
        task_3 = {'to': '0xDDB6DcCE6B794415145Eb5cAa6CD335AEdA9C272', 'amount': 0, 'gaslimit': 280000, 'data': data3}
        print(f"第{i+1}个任务: 执行Burn...")
        tx_hashes_3 = execute_tasks([task_3], [account], rpc)
        # 等待第三个任务完成
        tx_hash = tx_hashes_3[0]['result']
        receipt = rpc.eth.waitForTransactionReceipt(tx_hash)
        if receipt.status == 1:
            print(f"第{i+1}个任务: Burn已完成！")
        else:
            print(f"第{i+1}个任务: Burn失败！")

        # 任务4 Attack
        recipient_address = accounts[i][:-1].split(',')[0]
        data4 = '0xd018db3e' + account.address[2:].rjust(64,'0') + recipient_address[2:].rjust(64,'0')
        task_4 = {'to': '0xDDB6DcCE6B794415145Eb5cAa6CD335AEdA9C272', 'amount': 0, 'gaslimit': 280000, 'data': data4}
        print(f"第{i+1}个任务: 执行Attack...")
        tx_hashes_4 = execute_tasks([task_4], [account], rpc)
        # 等待第四个任务完成
        tx_hash = tx_hashes_4[0]['result']
        receipt = rpc.eth.waitForTransactionReceipt(tx_hash)
        if receipt.status == 1:
            print(f"第{i+1}个任务: Attack已完成！")
        else:
            print(f"第{i+1}个任务: Attack失败！")
        print(f"\033[1;31m第{i+1}个任务已完成！地址：{account.address}\033[0m")

    print("所有任务执行完毕。")
