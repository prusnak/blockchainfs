#!/usr/bin/python
import sys
import stat
import errno
import time
import re
from fuse import FUSE, FuseOSError, Operations
from insight import Insight

class DirEntry(object):

	def __init__(self):
		pass

	def stat(self):
		now = time.time()
		return dict(st_mode=(stat.S_IFDIR | 0755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=2)

class FileEntry(object):

	def __init__(self, data):
		self.data = data
		self.size = len(data)

	def stat(self):
		now = time.time()
		return dict(st_mode=(stat.S_IFREG | 0644), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=self.size)


class BlockchainFS(Operations):

	def __init__(self):
		self.fd = 0
		self.data = Insight()
		self.blockheight = self.data.blockheight()
		self.cache = {}
		self.cache['/'] = DirEntry()

	def open(self, path, flags):
		self.fd += 1
		return self.fd

	def statfs(self, path):
		return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

	def getattr(self, path, fh=None):
		if path in self.cache:
			return self.cache[path].stat()
		raise FuseOSError(errno.ENOENT)

	def read(self, path, size, offset, fh):
		if path in self.cache:
			return self.cache[path].data[offset:offset+size]
		return '\x00' * size

	def readdir(self, path, fh):

		if path == '/': # /
			l = ['%03dxxx' % x for x in range(0, self.blockheight / 1000 + 1)]
			for i in l:
				self.cache[path + i] = DirEntry()
			return ['.', '..'] + l

		if re.match(r'^/[0-9]{3}xxx$', path): # /000xxx
			offset = int(path[1:4])
			l = ['%06d' % x for x in range(offset * 1000, min((offset + 1)* 1000, self.blockheight + 1))]
			for i in l:
				self.cache[path + '/' + i] = DirEntry()
			return ['.', '..'] + l

		if re.match(r'^/[0-9]{3}xxx/[0-9]{6}$', path): # /000xxx/000000
			blockhash = self.data.blockhash_by_index(int(path[8:14]))
			blockinfo = self.data.blockinfo(blockhash)
			toadd = {
				'blockhash'         : FileEntry(blockhash),
				'bits'              : FileEntry(str(blockinfo['bits'])),
				'chainwork'         : FileEntry(str(blockinfo['chainwork'])),
				'confirmations'     : FileEntry(str(blockinfo['confirmations'])),
				'difficulty'        : FileEntry(str(blockinfo['difficulty'])),
				'merkleroot'        : FileEntry(str(blockinfo['merkleroot'])),
				'nextblockhash'     : FileEntry(str(blockinfo['nextblockhash'])),
				'nonce'             : FileEntry(str(blockinfo['nonce'])),
				'previousblockhash' : FileEntry(str(blockinfo['previousblockhash'])),
				'reward'            : FileEntry(str(blockinfo['reward'])),
				'size'              : FileEntry(str(blockinfo['size'])),
				'time'              : FileEntry(str(blockinfo['time'])),
				'transactions'      : FileEntry(str(len(blockinfo['tx']))),
				'version'           : FileEntry(str(blockinfo['version']))
			}
			for tx in blockinfo['tx']:
				toadd[tx] = DirEntry()
			for i in toadd:
				self.cache[path + '/' + i] = toadd[i]
			return ['.', '..'] + toadd.keys()

		if re.match(r'^/[0-9]{3}xxx/[0-9]{6}/[0-9a-f]{64}$', path): # /000xxx/000000/ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
			txinfo = self.data.txinfo(path[-64:])
			toadd = {
				'fee'       : FileEntry(str(txinfo['fees'])),
				'inputs'    : FileEntry(str(len(txinfo['vin']))),
				'locktime'  : FileEntry(str(txinfo['locktime'])),
				'outputs'   : FileEntry(str(len(txinfo['vout']))),
				'size'      : FileEntry(str(txinfo['size'])),
				'time'      : FileEntry(str(txinfo['time'])),
				'version'   : FileEntry(str(txinfo['version'])),
				'value_in'  : FileEntry(str(txinfo['valueIn'])),
				'value_out' : FileEntry(str(txinfo['valueOut']))
			}
			# TODO: process vin/vout structure
			for i in toadd:
				self.cache[path + '/' + i] = toadd[i]
			return ['.', '..'] + toadd.keys()

		return ['.', '..']


def main():
	if len(sys.argv) != 2:
		print('usage: %s <mountpoint>' % sys.argv[0])
		sys.exit(1)
	fuse = FUSE(BlockchainFS(), sys.argv[1], foreground=True, fsname='blockchainfs')

if __name__ == '__main__':
	main()
