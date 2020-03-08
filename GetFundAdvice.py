import requests
import json
import sys
import os
from operator import itemgetter, attrgetter
from email_send import send_email

#从json文件中读取邮箱信息，以及关注基金的数据
def ReadJson(fundFile, setFile):
    with open( fundFile, encoding='utf-8') as f:
        fund_json_data = json.load(f)
        f.close()
    with open( setFile, encoding='utf-8') as f:
        set_json_data = json.load(f)
        f.close()
    
    from_addr = set_json_data["from_addr"]
    password = set_json_data["password"]
    receive_email = set_json_data["receive_email"].split(",")
    funds = fund_json_data["funds"] #关心的基金数据
    
    return funds, from_addr, password, receive_email

#解析文件中的基金数据
# funds_datas = dict() #通过基金编号查询基金信息， <基金编号, 基金数据(Node, Name, WantedValue, OwnerBY)>
# owner_funds #用于查询每个人所持有的基金. <持有人, map(持有基金的编号, 持仓成本)>
def PraseFundsData(funds):
    funds_datas = dict() #map， <基金编号, 基金数据>
    owner_funds = dict() #map, <持有人, map(持有基金的编号, 持仓成本)>
    for fund in funds:
        funds_datas[fund["Code"]] = fund
        
        own_list = fund["OwnerBY"]
        if len(own_list) > 0:
            for list_item in own_list:
                own_name = list_item["OwnName"]
                own_cost = list_item["Cost"]
                if own_name not in owner_funds:
                    owner_funds[own_name] = dict()
                
                owner_funds[own_name][fund["Code"]] = own_cost
        
    return funds_datas, owner_funds

#从接口获取基金当前的单位净值以及涨幅情况. 周内11:55,14:30,22:00查询三次，其中22:00晚上这一次直接查准确净值，不用查询估值
#fund_earn_map 用于将基金按涨幅由低向高排序
def GetFundsInfo(funds_datas, night_check = False):
    #url="http://fundgz.1234567.com.cn/js/{0}.js" #一个备选的url
    url = "http://fundex2.eastmoney.com/FundWebServices/MyFavorInformation.aspx?t=kf&s=desc&sc=&pstart=0&psize=10000&fc={0}"
    fund_earn_map = dict() #map, <基金编号, 编号>, 排序用
    
    for fund_code in funds_datas.keys():
        rcv_data = requests.get(url.format(fund_code)).json()
        data_info_map = rcv_data[0] #通过接口获得的基金事实数据. 对应关系见下面func_dict
        
        if night_check:
            funds_datas[fund_code]["CurValue"] = data_info_map["dwjz"] #单位净值
            funds_datas[fund_code]["EarningRate"] = data_info_map["rzzl"]   #日涨幅度
        else:
            funds_datas[fund_code]["CurValue"] = data_info_map["gsz"] #当前估值
            funds_datas[fund_code]["EarningRate"] = data_info_map["gszzl"]   #接口返回的估算涨幅
        
        fund_earn_map[fund_code] = float(funds_datas[fund_code]["EarningRate"])
    
    sorted(fund_earn_map.items(), key = lambda item:item[1]) #按收益率从低往高排序
    
    return fund_earn_map

#用于计算涨跌幅比率
#pre_val:原值, str
#cur_val:现值，str
def CalRate(pre_val, cur_val):
    p_val = float(pre_val)
    c_val = float(cur_val)
    rate = float( '%0.4f' %((c_val - p_val) / p_val * 100))
    return str(rate)
    

#用于组装邮件发送数据
#funds_datas 基金的基本信息
#owner_funds 个人持有基金，单独输出，便于查看 <持有人, map(持有基金的编号, 持仓成本)>
#fund_earn_map 所有关注基金的情况, 按涨跌幅度由低向高排列
def BuildUpContent(funds_datas, owner_funds, fund_earn_map):
    content = ""
    split_line = "**********************{0}**********************\n"
    content_format = "{0}-{1}; 估值({2}),涨幅({3}%); 成本价({4}),收益率({5}%); 期望低价[{6}]\n"#编号-名称-现值-涨幅, (持仓价-收益率), [期待的低价]
    #个人持有情况
    for own_name, fund_cost_map in owner_funds.items(): 
        content = content + split_line.format(own_name+"持有")
        for fund_code, cost in fund_cost_map.items():
            data = funds_datas[fund_code]
        
            content += content_format.format(data["Code"], data["Name"], data["CurValue"], data["EarningRate"],\
                                             cost, CalRate(cost, data["CurValue"]), data["WantedValue"])
    
    #关注的基金情况
    content = content + split_line.format("当前行情")
    
    sorted_list = sorted(fund_earn_map.items(), key=itemgetter(1))#将收益率按从低往高排列
    for item in sorted_list:
        data = funds_datas[item[0]]
        
        content += content_format.format(data["Code"], data["Name"], data["CurValue"], data["EarningRate"],\
                                         "", "", data["WantedValue"])#持仓成本价和收益率为空
    
    return content


def main(argv):
    path = ""
    path = os.path.abspath(path)
    
    split_char = '/'
    if sys.platform == 'win32':
        split_char = '\\'
    
#    fundFile = path + split_char + "funds.json"
#    setFile = path + split_char + "setting.json"
    
    fundFile = "/root/MyFundsTools/funds.json"
    setFile = "/root/MyFundsTools/setting.json"
    
    print(fundFile, setFile)
    
    night_check = False
    if (len(argv) > 1 and argv[1] == "1"):
        night_check = True #晚上十点的那次查询
    
    funds, from_addr, password, receive_email = ReadJson(fundFile, setFile)

    funds_datas, owner_funds = PraseFundsData(funds)
    
    fund_earn_map = GetFundsInfo(funds_datas, True)
    
    content = BuildUpContent(funds_datas, owner_funds, fund_earn_map)
    
    send_email(from_addr, password, content, receive_email)
    
    
    
    
if __name__ == "__main__":
    main(sys.argv)


# 基金字典对应关系
fund_dict = {
    'gztime': u'估值时间',
    'gszzl': u'估算涨幅',
    'gsz': u'估算净值',
    
    'dwjz': u'单位净值',
    'ljjz': u'累计净值',
    'rzzl': u'日增长率',
    'syl': u'收益率',
    
    'shzt': u'赎回状态',
    'name': u'基金名称',
    'jjlx': u'基金类型',
    'jzrq': u'净值日期',
    'sgzt': u'申购状态',
    'fundcode': u'基金编号',
    'isgz': '',
    'htpj': '',
    'nkfr': '',
    'isbuy': '1'
}