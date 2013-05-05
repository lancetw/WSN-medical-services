# -*- coding: utf-8 -*-
# lancetw aka Hsin-lin Cheng <lancetw@gmail.com>

import random
import time

from hashlib import sha224

# Hash(．)
def H(data):
	return sha224(data).hexdigest()

# 金鑰產生器
def gen_key():
	return H( str(random.getrandbits(256)) )

# XOR 函數
from itertools import izip, cycle
def XOR(key, data):
	return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle(key)))

# 產生裝置的 MAC address
def gen_node_id():
	mac = [ 0x00, 0x16, 0x3e,
		random.randint(0x00, 0x7f),
		random.randint(0x00, 0xff),
		random.randint(0x00, 0xff) ]
	return ':'.join(map(lambda x: "%02x" % x, mac))

# n: 隨機數數量, total: 隨機數的總和
def rand_num_list(n, total):
	dividers = sorted(random.sample(xrange(1, total), n - 1))
	return [a - b for a, b in zip(dividers + [total], [0] + dividers)]

####### === $ 前置定義區 $ === #######

# 時間測量
time_test = {}

n = dict()
# 醫院的樓層數
n['floors'] = 5
# 初始樓層匯聚節點編號
FSinkID = list()
for i in range(n['floors']):
	FSinkID.append( gen_node_id() )
# 初始金鑰數量
n['keys'] = 30
# 初始感測節點數量與編號
n['wsns_total'] = 1000
rnd = rand_num_list(n['floors'], n['wsns_total'])
n['wsns'] = list()
SID = list()
for i in range(n['floors']):
	_wsn = rnd[i]
	n['wsns'].append( _wsn )
	for j in range(_wsn):
		SID.append( gen_node_id() )
# 金鑰池
P = list()
# 隨機數
R = list()
for i in range(n['wsns_total']):
	R.insert( i, str(random.randint(3, 65537)) )
	
# 系統管理員密鑰 (sha224)
K_admin = '86a9c7e6d1d263e5419d0eb0fa12ede100bf482e640ddc2073947e8a'


####### === $ 金鑰伺服器產生金鑰階段 $ === #######
#@ 測量時間 - 開始
time_start = time.time()

# 產生 n 把金鑰儲存到金鑰池中
for i in range(n['keys']):
	key = gen_key()
	P.insert( i, key )

# 從金鑰池中挑出金鑰 GK[w]，以此產生金鑰鍊 SK[w] 給每個樓層的匯聚節點
GK = list()
SK = list()
for w in range(n['floors']):
	s = 0
	_GK = P.pop()
	GK.insert( w, _GK )
	SK.insert( w, H(XOR(GK[w], R[s])) )
	# 印出過程
	#print 'SK[%d] = H(%s ⊕ %s)' % (w, _GK, R[s])
	s += 1
	
# 以金鑰鍊產生獨一無二的子金鑰，配發給每個無線感測節點
# SKI 紀錄每層樓各自的子金鑰表（子金鑰用來加密生理資訊）
SKI = list()
for w in range(n['floors']):
	sub_SK = list()
	i = n['wsns'][w]
	n_keys = n['keys'] - 1
	_SK = H(XOR(SK[w], R[n_keys]))
	for j in range(i):
		_SK_old = _SK
		_SK = H(XOR(_SK, R[n_keys]))
		sub_SK.append( _SK )
		# 印出過程
		#print 'F%d: SK= %s = H(%s ⊕ %s)' % (w+1, _SK, _SK_old, R[n_keys])
		n_keys -= 1
	SKI.append( sub_SK )

#@ 測量時間 - 結束
time_end = time.time()
time_test['key_server_gen_key_phase'] = (time_end - time_start)

####### === $ 病患入院無線感測節點配置階段 $ === #######
#@ 測量時間 - 開始
time_start = time.time()

# PKIW 為會議金鑰，用來進行金鑰更換時使用，PKIW[i][w], i: 第 i 個感測節點, w: 樓層
PKIW = list()
for w in range(n['floors']):
	sub_PK = list()
	for i in range(n['wsns'][w]):
		_PK = H(SID[i] + FSinkID[w] + K_admin)
		sub_PK.append( _PK )
		# 印出過程
		#print 'F%d: PK[%d][%d] = %s = H(%s || %s || %s)' % (w+1, i, w, _PK, SID[i], FSinkID[w], K_admin)
	PKIW.append( sub_PK )

#@ 測量時間 - 結束
time_end = time.time()
time_test['WSN_setup_phase'] = (time_end - time_start)


# 輸出結果
print '=' * 80
print '醫院總樓層數：%d 層' % n['floors']
print '初始金鑰數：%d 把' % n['keys']
print '無線感測節點數：%d 台' % n['wsns_total']
print '-' * 80
print 'SK[w] = H(GK[w] ⊕ R[s])'
print 'SK[i-1] = H(SK[w] ⊕ R[n]), SK[i-2] = H(SK[i-1] ⊕ R[n-1]) ... SK[0] = H(SK[1] ⊕ R[1])'
print '金鑰伺服器產生金鑰階段 - 花費時間：%f 秒' % time_test['key_server_gen_key_phase']
print '-' * 80
print 'PK[i][w] = H(SID[i] || FSinkID[w] || K_admin)'
print '病患入院無線感測節點配置階段 - 花費時間：%f 秒' % time_test['WSN_setup_phase']
