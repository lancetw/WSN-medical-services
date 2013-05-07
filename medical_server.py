# -*- coding: utf-8 -*-
# 無線感測醫療資訊系統環境效能模擬
# lancetw aka Hsin-lin Cheng <lancetw@gmail.com>

import random
import time

####### === $ 函式區 $ === #######

# Hash(．)
from hashlib import sha256
def H(data):
	return sha256(data).hexdigest()

# 金鑰產生器
def gen_key():
	return H( str(random.getrandbits(256)) )

# XOR 函數
from itertools import izip, cycle
def XOR(key, data):
	return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle(key)))
	
# 子金鑰加密用 MAC
def MAC(key, msg):
	return
	
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
	
# 一般隨機浮點數
def randrange_float(start, stop, step):
    return random.randint(0, int((stop - start) / step)) * step + start

# 初始化系統變數
def init(floors=None, keys=None, wsns_total=None):
	# 初始化變數
	if floors != None: n['floors'] = floors
	if keys != None: n['keys'] = keys
	if wsns_total != None: n['wsns_total'] = wsns_total
	# 給每樓層的匯聚節點設定 MAC Address
	for w in range(n['floors']):
		FSinkID.append( gen_node_id() )
	# 為每樓層產生隨機個感測節點數	
	rnd = rand_num_list(n['floors'], n['wsns_total'])
	# 給所有的感測節點設定 MAC Address
	for w in range(n['floors']):
		_wsn = rnd[w]
		n['wsns'].append( _wsn )
		for j in range(_wsn):
			SID.append( gen_node_id() )
	# 產生隨機數
	for i in range(n['keys'] * n['floors'] + n['wsns_total']):
		R.insert( i, str(random.randint(3, 65537)) )


####### === $ 金鑰伺服器產生金鑰階段 $ === #######

def WSN_gen_key_phase():
	# 產生 n 把金鑰儲存到金鑰池中
	for i in range(n['keys']):
		key = gen_key()
		P.insert( i, key )

	# 從金鑰池中挑出金鑰 GK[w]，以此產生金鑰鍊 SK[w] 給每個樓層的匯聚節點
	GK = list()
	for w in range(n['floors']):
		s = 0
		_GK = P.pop()
		GK.insert( w, _GK )
		SK.insert( w, H(XOR(GK[w], R[s])) )
		# 印出過程
		#print 'SK[%d] = H(%s ⊕ %s)' % (w, _GK, R[s])
		s += 1
		
	# 以金鑰鍊產生獨一無二的子金鑰，配發給每個無線感測節點
	for w in range(n['floors']):
		sub_SK = list()
		i = n['wsns'][w]
		n_keys = n['keys']
		_SK = H(XOR(SK[w], R[n_keys]))
		for j in range(i):
			_SK_old = _SK
			_SK = H(XOR(_SK, R[n_keys]))
			sub_SK.append( _SK )
			# 印出過程
			#print 'F%d: SK= %s = H(%s ⊕ %s)' % (w+1, _SK, _SK_old, R[n_keys])
			n_keys -= 1
		SKx.append( sub_SK )


####### === $ 病患入院無線感測節點配置階段 $ === #######

def WSN_setup_phase():
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
		
		
####### === $ 無線醫護感測節點日常運作程序 - 每日定期蒐集生理資訊 $ === #######
# 產生生理資訊
def gen_phinfo_M():
	for i in range(n['wsns_total']):
		# p: 脈搏, bp: 血壓, bt: 體溫, ecg: 心電圖
		d = {'id': SID[i], 'p': randrange_float(40, 200, 1), 'bp': randrange_float(60, 250, 0.1), 'bt': randrange_float(36, 45, 0.1), 'ecg': open('s0028lre.xyz', 'rb').read()}
		M.append(d)
	return M

# phinfo_list: 輸入生理資訊列表
def WSN_daily_collect_info_process():
	packets = list()
	def _send(i, data):
		packets.insert(i, data)
	
	def _recv(i):
		return packets[i]

	# 樓層匯聚節點開始要求各節點回報生理資訊
	for w in range(n['floors']):
		# 匯聚節點送出請求 SK 給每個無線感測節點，使用 SKx 加解密
		_SKx = SKx[w]
		Mp = 'MSG TEST'
		for i in range(n['wsns'][w]):
			d = {'encrypted': MAC(_SKx[i], Mp), 'plaintext': Mp}
			_send(i, d)
			
		# 模擬子節點取得資訊
		for i in range(n['wsns'][w]):
			d = _recv(i)
			plaintext = d['plaintext']
			print MAC(_SKx[i], d['encrypted'])
			print '-' * 80
			print plaintext
			print '-' * 80
			print cmp( MAC(_SKx[i], d['encrypted']), plaintext )
			print '-' * 80
				
	
	
		

####### === $ 變數定義區 $ === #######

# 時間測量
time_test = {}
# 資料暫存陣列
n = dict()
# 醫院的樓層數
n['floors'] = 5
# 初始樓層匯聚節點編號
FSinkID = list()
# 初始金鑰數量
n['keys'] = 30
# 初始感測節點數量與編號
n['wsns_total'] = 1000
n['wsns'] = list()
SID = list()
# 金鑰池
P = list()
# 隨機數
R = list()
# 匯聚節點金鑰
SK = list()
# 無線感測節點子金鑰（子金鑰用來加密生理資訊）
SKx = list()
# 系統管理員密鑰 (sha256)
K_admin = "86a9c7e6d1d263e5419d0eb0fa12ede100bf482e640ddc2073947e8a"
# 生理資訊暫存
M = list()

####### === $ 主程式 $ === #######

def main():
	def run_once(floors=7, keys=50, wsns_total=1000, output=False):
		# 初始化變數
		init(floors, keys, wsns_total)
		
		#@ 測量時間 - 開始
		time_start = time.time()
		WSN_gen_key_phase()
		#@ 測量時間 - 結束
		time_end = time.time()
		time_test['WSN_gen_key_phase'] = (time_end - time_start)
		
		#@ 測量時間 - 開始
		time_start = time.time()
		WSN_setup_phase()
		#@ 測量時間 - 結束
		time_end = time.time()
		time_test['WSN_setup_phase'] = (time_end - time_start)
		
		gen_phinfo_M()
		WSN_daily_collect_info_process()
		
		if output == True:
			output_ans()
		else:
			return time_test
	
	def output_ans():
		# 輸出結果
		print '=' * 80
		print '醫院總樓層數：%d 層 |' % n['floors'],
		print '初始金鑰數：%d 把 |' % n['keys'],
		print '無線感測節點數：%d 台' % n['wsns_total']
		print '-' * 80
		#print 'SK[w] = H(GK[w] ⊕ R[s])'
		#print 'SK[i-1] = H(SK[w] ⊕ R[n]), SK[i-2] = H(SK[i-1] ⊕ R[n-1]) ... SK[0] = H(SK[1] ⊕ R[1])'
		print '金鑰伺服器產生金鑰階段 - 花費時間：%f 秒' % time_test['WSN_gen_key_phase']
		print '-' * 80
		#print 'PK[i][w] = H(SID[i] || FSinkID[w] || K_admin)'
		print '病患入院無線感測節點配置階段 - 花費時間：%f 秒' % time_test['WSN_setup_phase']

	def run():
		scope = input("請輸入目標金鑰數上限，例如 3000：")
		key_n = input("請輸入每回產生幾組金鑰，例如 500：")
		floor_n = input("請輸入醫療大樓樓層總數（固定），例如 10：")
		wsn_n = input("請輸入無線感測節點總數（固定），例如 1000：")
		
		print "請耐心等待，圖片產生中..."
		
		# 跑幾次
		max_run = (scope / key_n) + 1
		# 區間間隔多少
		spacing = key_n
		
		chart_data_x = list()
		chart_data_y1 = list()
		chart_data_y2 = list()
		
		for i in range(1, max_run):
			x = spacing * i
			ans = run_once(floor_n, x, wsn_n)
			y1 = ans['WSN_gen_key_phase']
			y2 = ans['WSN_setup_phase']
			chart_data_x.append(x)
			chart_data_y1.append(y1)
			chart_data_y2.append(y2) 
		
		# 畫圖表
		import numpy as np
		import matplotlib.pyplot as plt
		from matplotlib import rcParams
		# 微軟正黑體
		rcParams['font.family'] = 'Microsoft JhengHei'
		
		# 圖表 [金鑰伺服器產生金鑰階段]
		plt.figure(figsize=(8,5))
		plt.plot(chart_data_x, chart_data_y1, label=u"金鑰伺服器產生金鑰階段 - Performance", color="red", linewidth=2, marker='o', linestyle='-')
		plt.xlabel(u"初始金鑰數（個）")
		plt.ylabel(u"花費時間（秒）")
		plt.title(u"初始金鑰數與花費時間關係圖")
		plt.ylim(0, max(chart_data_y1) * 2)
		plt.legend()
		
		
		# 圖表 [病患入院無線感測節點配置階段]
		plt.figure(figsize=(8,5))
		plt.plot(chart_data_x, chart_data_y2, label=u"病患入院無線感測節點配置階段 - Performance", color="red", linewidth=2, marker='o', linestyle='-')
		plt.xlabel(u"初始金鑰數（個）")
		plt.ylabel(u"花費時間（秒）")
		plt.title(u"初始金鑰數與花費時間關係圖")
		plt.ylim(0, max(chart_data_y2) * 2)
		plt.legend()
		
		# 顯示所有圖表
		plt.show()
		
		print "圖表產生完成！"
		
	run()

if  __name__ =='__main__':main()
