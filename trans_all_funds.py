import requests
import heapq
import sys
import datetime
from multiprocessing import Process, Pool

class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._index = 0

    def push(self, item, priority):
        heapq.heappush(self._queue, (-priority, self._index, item))
        self._index += 1

    def pop(self):
        return heapq.heappop(self._queue)[-1]

    def size(self):
        return len(self._queue)

#基金前两位一般是交易所或者组织的编号
def TransFunds(head_num, up_pri_qu, down_pri_qu):
    today = datetime.date.today() #今天日期
    head_code = str(head_num).zfill(2) #前两位

    for cnt in range(5):#后四位,每批200个的取
        url = "http://fundex2.eastmoney.com/FundWebServices/MyFavorInformation.aspx?t=kf&s=desc&sc=&pstart=0&psize=10000&fc="
        for code in range(cnt*200+1, (cnt+1)*200): #一批取250个数据
            func_code = head_code + str(code).zfill(4)
            url = url + func_code + ","

        rcv_data = requests.get(url).json()#url.format(func_code)
        for data_info in rcv_data:# 通过接口获得的基金数据,一批有多个. 对应关系见下面func_dict
            if data_info["gszzl"] == "" or data_info["gztime"] < today.strftime('%Y-%m-%d'):
                continue

            tmp_dict = dict()
            tmp_dict["Code"] = data_info["fundcode"]
            tmp_dict["Name"] = data_info["name"]
            tmp_dict["EarningRate"] = data_info["gszzl"]
            tmp_dict["CurValue"] = data_info["gsz"]
            tmp_dict["Time"] = data_info["gztime"]

            up_pri_qu.push(tmp_dict, float(tmp_dict["EarningRate"])) #从小到大排列, 每次保留最大的前十个
            if up_pri_qu.size() > 10:#维持10个
                up_pri_qu.pop()

            down_pri_qu.push(tmp_dict, -float(tmp_dict["EarningRate"])) #负数代表从大到小排列. 每次保留最小的前十个
            if down_pri_qu.size() > 10:#维持10个
                down_pri_qu.pop()
    print(down_pri_qu.size())
    print(up_pri_qu.size())

#遍历000001~999999的所有基金,获取其当日涨跌幅情况
def TraverseAllFunds(down_top_10, up_top_10):
    down_pri_qu = PriorityQueue()
    up_pri_qu = PriorityQueue()
    for i in range(100):#头两位, 01-99
        print("Progress:", i)
        TransFunds(i, down_pri_qu, up_pri_qu)

    for i in range(10):
        down = down_pri_qu.pop()
        down_top_10.append(down)
        up = up_pri_qu.pop()
        up_top_10.append(up)

def main(argv):
    down_top_10 = []
    up_top_10 = []
    TraverseAllFunds(down_top_10, up_top_10)  # 遍历所有基金净值

    content = ""
    split_line = "**********************{0}**********************\n"
    #跌幅榜前十
    content = content + split_line.format("跌幅榜单")
    content_format = "{0}-{1}; 估值({2}),跌幅({3}%); 估算时间({4})\n"  # 编号-名称-现值-涨幅-估算时间
    for data in down_top_10:
        content += content_format.format(data["Code"], data["Name"], data["CurValue"], data["EarningRate"], data["Time"])

    # 涨幅榜前十
    content = content + split_line.format("涨幅榜单")
    content_format = "{0}-{1}; 估值({2}),涨幅({3}%); 估算时间({4})\n"  # 编号-名称-现值-涨幅-估算时间
    for data in up_top_10:
        content += content_format.format(data["Code"], data["Name"], data["CurValue"], data["EarningRate"], data["Time"])

    print(content)

if __name__ == "__main__":
    main(sys.argv)