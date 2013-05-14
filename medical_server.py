# -*- coding: utf-8 -*-
# 無線感測醫療資訊系統環境效能模擬
# lancetw aka Hsin-lin Cheng <lancetw@gmail.com>

import time

####### === $ 函式區 $ === #######

# Hash(．)
from hashlib import sha256
def H(data):
	return sha256(data).digest()

# XOR 函數
from Crypto.Cipher import XOR as _XOR
def XOR(key, msg, mode=None):
	xor = _XOR.new(key)
	if mode == 'encrypt':
		return xor.encrypt(msg)
	if mode == 'decrypt':
		return xor.decrypt(msg)

# AES Class
import base64
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Random import random
BS = AES.block_size
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(s[-1])]
class AESCipher:
    def __init__(self, key):
        self.key = key 

    def encrypt(self, raw):
        raw = pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) ) 

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[AES.block_size:] ))

# 通用金鑰產生器
def gen_key():
	return Random.new().read(32)

# 子金鑰加密用 MAC
def MAC(key, msg, crypt_type=None, mode=None):
	if crypt_type == None:
		return msg
	
	if crypt_type == 'XOR':
		return XOR(key, msg, mode)
		
	if crypt_type == 'AES':
		aes = AESCipher(key)
		if mode == 'encrypt':
			return aes.encrypt(msg)
		elif mode == 'decrypt':
			return aes.decrypt(msg)
		else:
			return aes.encrypt(msg)
	
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
def init_static(floors=None, wsns_total=None):
	# 初始化變數
	if floors != None: n['floors'] = floors
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

# 初始化系統變數
def init(floors=None, keys=None, wsns_total=None):
	# 初始化變數
	if floors != None: n['floors'] = floors
	if keys != None: n['keys'] = keys
	if wsns_total != None: n['wsns_total'] = wsns_total
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
		SK.insert( w, H(XOR(GK[w], R[s], 'encrypt')) )
		# 印出過程
		#print 'SK[%d] = %s = H(%s ⊕ %s)' % (w+1, str(SK[w]), str(GK[w]), R[s])
		s += 1
		
	# 以金鑰鍊產生獨一無二的子金鑰，配發給每個無線感測節點
	for w in range(n['floors']):
		sub_SK = list()
		i = n['wsns'][w]
		n_keys = n['keys']
		_SK = H(XOR(SK[w], R[n_keys], 'encrypt'))
		for j in range(i):
			_SK_old = _SK
			_SK = H(XOR(_SK, R[n_keys], 'encrypt'))
			sub_SK.append( _SK )
			# 印出過程
			#print 'F%d: SK= %s = H(%s ⊕ %s)' % (w+1, str(_SK), str(_SK_old), R[n_keys])
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
			#print 'F%d: PK[%d][%d] = %s = H(%s || %s || %s)' % (w+1, i, w, str(_PK), SID[i], FSinkID[w], str(K_admin))
		PKIW.append( sub_PK )
		
		
####### === $ 無線醫護感測節點日常運作程序 - 每日定期蒐集生理資訊 $ === #######
# 產生生理資訊
def gen_phinfo_M():
	ecg_bin = open('s0028lre.xyz', 'rb').read()
	for i in range(n['wsns_total']):
		# p: 脈搏, bp: 血壓, bt: 體溫, ecg: 心電圖
		d = {'id': SID[i], 'p': randrange_float(40, 200, 1), 'bp': randrange_float(60, 250, 0.1), 'bt': randrange_float(36, 45, 0.1), 'ecg': ecg_bin}
		M.append( str(d) )
		print '%d..' % (i+1),
	print '\n'
	return M

# phinfo_list: 輸入生理資訊列表
def WSN_daily_collect_info_process(crypt_type=None):
	packets = list()
	phyinfo = list()
	def _send(i, data):
		packets.insert(i, data)
	
	def _recv(i):
		return packets[i]
		
	def _save(i, data):
		phyinfo.insert(i, data)

	# 樓層匯聚節點開始要求各節點回報生理資訊
	for w in range(n['floors']):
		# 匯聚節點送出請求 SK 給每個無線感測節點，使用 SKx 加解密
		_SKx = SKx[w]
		Mp = 'MSG:PHYDATA_REQUEST FROM Side %i' % w
		for i in range(n['wsns'][w]):
			d = {'encrypted': MAC(_SKx[i], Mp, crypt_type, 'encrypt'), 'plaintext': Mp}
			_send(i, d)
		
		# 模擬子節點取得資訊
		for i in range(n['wsns'][w]):
			d = _recv(i)
			if ( cmp( MAC(_SKx[i], d['encrypted'], crypt_type, 'decrypt'), d['plaintext'] ) == 0):
				# 加密生理資訊
				d = {'encrypted': MAC(_SKx[i], M[i], crypt_type, 'encrypt'), 'plaintext': M[i]}
				_send(i, d)
	
		# 模擬匯聚節點接收資訊
		for i in range(n['wsns'][w]):
			d = _recv(i)
			if ( cmp( MAC(_SKx[i], d['encrypted'], crypt_type, 'decrypt'), d['plaintext'] ) == 0):
				_save(i, d['plaintext'])
			
		
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
# 生理資訊暫存
M = list()
# 系統管理員密鑰 (sha256)
K_admin = sha256('live long and prosper').digest()

####### === $ 主程式 $ === #######

def main():
	def run_once(floors=7, keys=50, wsns_total=1000, output=False):
		# 初始化變數
		print 'init()'
		init(floors, keys, wsns_total)
		
		print 'WSN_gen_key_phase()'
		#@ 測量時間 - 開始
		time_start = time.time()
		WSN_gen_key_phase()
		#@ 測量時間 - 結束
		time_end = time.time()
		time_test['WSN_gen_key_phase'] = (time_end - time_start)
		
		print 'WSN_setup_phase()'
		#@ 測量時間 - 開始
		time_start = time.time()
		WSN_setup_phase()
		#@ 測量時間 - 結束
		time_end = time.time()
		time_test['WSN_setup_phase'] = (time_end - time_start)

		print 'WSN_daily_collect_info_process()'
		#@ 測量時間 - 開始
		time_start = time.time()
		WSN_daily_collect_info_process()
		#@ 測量時間 - 結束
		time_end = time.time()
		time_test['WSN_daily_process_no_decrypted'] = (time_end - time_start)
		
		#@ 測量時間 - 開始
		time_start = time.time()
		WSN_daily_collect_info_process('XOR')
		#@ 測量時間 - 結束
		time_end = time.time()
		time_test['WSN_daily_process_XOR'] = (time_end - time_start)
		
		#@ 測量時間 - 開始
		time_start = time.time()
		WSN_daily_collect_info_process('AES')
		#@ 測量時間 - 結束
		time_end = time.time()
		time_test['WSN_daily_process_AES'] = (time_end - time_start)
		
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
		scope = input("請輸入目標金鑰數上限，例如 6000：")
		key_n = input("請輸入每回產生幾組金鑰，例如 1200：")
		floor_n = input("請輸入醫療大樓樓層總數（固定），例如 15：")
		wsn_n = input("請輸入無線感測節點總數（固定），例如 1000：")
		
		print '請耐心等待，圖片產生中...'
		
		# 跑幾次
		max_run = (scope / key_n) + 1
		# 區間間隔多少
		spacing = key_n
		
		chart_data_x = list()
		chart_data_y1 = list()
		chart_data_y2 = list()
		chart_data_y3 = list()
		chart_data_y4 = list()
		chart_data_y5 = list()
		
		# 初始化
		print '#初始化 init_static()'
		init_static(floor_n, wsn_n)
		
		# 準備生理資料
		print '#準備 %d 組生理資料 gen_phinfo_M()' % wsn_n
		gen_phinfo_M()
		
		for i in range(1, max_run):
			print '-' * 80
			print 'Run %d/%d' % (i, max_run-1)
			print '-' * 80
			x = spacing * i
			ans = run_once(floor_n, x, wsn_n)
			y1 = ans['WSN_gen_key_phase']
			y2 = ans['WSN_setup_phase']
			y3 = ans['WSN_daily_process_no_decrypted']
			y4 = ans['WSN_daily_process_XOR']
			y5 = ans['WSN_daily_process_AES']
			chart_data_x.append(x)
			chart_data_y1.append(y1)
			chart_data_y2.append(y2)
			chart_data_y3.append(y3)
			chart_data_y4.append(y4)
			chart_data_y5.append(y5)
		
		# 畫圖表
		import numpy as np
		import matplotlib.pyplot as plt
		from matplotlib import rcParams
		# 微軟正黑體
		rcParams['font.family'] = 'Microsoft JhengHei'
		
		# 圖表 [金鑰伺服器產生金鑰階段]
		plt.figure(figsize=(8,5))
		plt.plot(chart_data_x, chart_data_y1, label=u"Performance", color="red", linewidth=2, marker='o', linestyle='-')
		plt.xlabel(u"初始金鑰數（個）")
		plt.ylabel(u"花費時間（秒）")
		plt.title(u"「初始金鑰」數量與「金鑰伺服器產生金鑰階段」花費時間關係圖")
		plt.ylim(0, max(chart_data_y1) * 1.5)
		plt.legend()
		
		# 圖表 [病患入院無線感測節點配置階段]
		plt.figure(figsize=(8,5))
		plt.plot(chart_data_x, chart_data_y2, label=u"Performance", color="red", linewidth=2, marker='o', linestyle='-')
		plt.xlabel(u"初始金鑰數（個）")
		plt.ylabel(u"花費時間（秒）")
		plt.title(u"「初始金鑰」數量與「病患入院無線感測節點配置階段」花費時間關係圖")
		plt.ylim(0, max(chart_data_y2) * 1.5)
		plt.legend()
		
		# 圖表 [每日定期蒐集生理資訊]
		plt.figure(figsize=(8,5))
		plt.plot(chart_data_x, chart_data_y3, label=u"（無加密）- Performance", color="red", linewidth=2, marker='o', linestyle='-')
		plt.plot(chart_data_x, chart_data_y4, label=u"（XOR）- Performance", color="blue", linewidth=2, marker='o', linestyle='-')
		plt.plot(chart_data_x, chart_data_y5, label=u"（AES）- Performance", color="green", linewidth=2, marker='o', linestyle='-')
		plt.xlabel(u"初始金鑰數（個）")
		plt.ylabel(u"花費時間（秒）")
		plt.title(u"「初始金鑰」數量與「每日定期蒐集生理資訊」花費時間關係圖")
		plt.ylim(0, max(chart_data_y3 + chart_data_y4 + chart_data_y5) * 1.5)
		plt.legend()
		
		print '圖表產生完成！'
		# 顯示所有圖表
		plt.show()
		
		
		
	run()

if  __name__ =='__main__':main()
