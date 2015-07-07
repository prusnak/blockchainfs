import requests

APIURL = 'https://insight.bitpay.com/api'

class Insight(object):

	def blockheight(self):
		r = requests.get('%s/sync' % APIURL)
		if r.status_code == 200:
			return r.json()['height']
		else:
			return 0

	def blockhash_by_index(self, index):
		r = requests.get('%s/block-index/%d' % (APIURL, index))
		if r.status_code == 200:
			return str(r.json()['blockHash'])
		else:
			return ''

	def blockinfo(self, blockhash):
		r = requests.get('%s/block/%s' % (APIURL, blockhash))
		if r.status_code == 200:
			return r.json()
		else:
			return {}

	def txinfo(self, txhash):
		r = requests.get('%s/tx/%s' % (APIURL, txhash))
		if r.status_code == 200:
			return r.json()
		else:
			return {}
