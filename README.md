使用说明：
安装python库，如web3等，运行的时候自己看缺少什么库就安装一下。
在cat.py同级目录下创建两个文件:
wallet.txt(存放你的钱包密钥，每行一个),
wallet2.txt(存放生成的空钱包，可以使用wallet.py生成，需要多少生成多少）,
注意:两个文件里的行数必须一样，因为你wallet.txt里需要交互的地址是要往wallet2.txt里的钱包地址发送Nft等操作的，wallet2.txt里的钱包地址就是工具人的作用。

运行方法：py cat.py

