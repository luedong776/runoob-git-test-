# -*- coding: UTF-8 -*-

from fractions import Fraction
import random
import requests
import urllib2
import json

# -------------------------------公用模块-------------------------------
# 添加流表
def add_flow_entry(dpid,match,priority,actions):
    url = "http://127.0.0.1:8080/stats/flowentry/add"
    post_data = "{'dpid':%s,'match':%s,'priority':%s,'actions':%s}" % (dpid,str(match),priority,str(actions))
    req = urllib2.Request(url,post_data)
    res = urllib2.urlopen(req)
    return res.getcode()

# 查看links
def get_all_links():
    url = "http://127.0.0.1:8080/v1.0/topology/links"
    req = requests.get(url)
    res = req.text
    res = json.loads(res)
    return res

# 建图
def get_graph():
    graph = {}
    links = get_all_links()

    for link in links:
        if (graph.get(int(link['src']['dpid'].encode('ascii')))):
            graph[int(link['src']['dpid'].encode('ascii'))].append(int(link['dst']['dpid'].encode('ascii')))
        else:
            graph[int(link['src']['dpid'].encode('ascii'))] = []
            graph[int(link['src']['dpid'].encode('ascii'))].append(int(link['dst']['dpid'].encode('ascii')))

    return graph

# 找到所有从start到end的路径
def findAllPath(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return [path]

    paths = []  # 存储所有路径
    for node in graph[start]:
        if node not in path:
            newpaths = findAllPath(graph, node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths

# 利用代价计算权重及区间
def weight_calculate(cost):
    weight = []
    # 区间
    interval = []
    total = 0
    sum = 0
    for cost_i in cost:
        weight.append(pow(cost_i,-1))
    for ele in range(0, len(weight)):
        # 权值求和
        total += weight[ele]
    for weight_i in weight:
        sum += weight_i
        interval.append(sum / total)
    # 区间右端点
    return interval

# 路由选择
def route(interval, paths):
    point = random.random()
    for i in range(0, len(interval)):
        if(point < interval[i]):
            return paths[i]

# -------------------------------带宽最大化模块-------------------------------

# 获取带宽利用率 TODO
def get_bandwidth():
    utilization = {1: {2: 0.4, 3: 0.6, 4: 0.8},
         2: {1: 0.4, 5: 0.3},
         3: {1: 0.6, 5: 0.4},
         4: {1: 0.8, 5: 0.2},
         5: {2: 0.3, 3: 0.4, 4: 0.2, 6: 0.3},
         6: {5: 0.3}
        }
    return utilization

# 计算源到汇所有路径的代价cost
def cost_calculate_bandwidth(paths, U):
    cost = []
    for path in paths:
        # 瓶颈链路利用率
        U_max = 0
        for i in range(len(path)-1):
            if(U[path[i]][path[i+1]] > U_max):
                U_max = U[path[i]][path[i+1]]
        # 计算cost
        if(U_max >= 0 and U_max < Fraction(1,3)):
            cost.append(10 * U_max)
        elif(U_max >= Fraction(1,3) and U_max < Fraction(2,3)):
            cost.append(30 * U_max)
        elif(U_max >= Fraction(2,3) and U_max < Fraction(9,10)):
            cost.append(100 * U_max)
        else:
            cost.append(700 * U_max)
    return cost

# 带宽最大化
def path_bandwidth(start, end, graph):
    utilization = get_bandwidth()
    paths = findAllPath(graph, start, end)
    interval = weight_calculate(cost_calculate_bandwidth(paths, utilization))
    path = route(interval, paths)
    return path

# -------------------------------QoS模块-------------------------------

# 获取时延和丢包 TODO
def get_data():
    # 单位ms
    delay = {1: {2: 20, 3: 10, 4: 20},
         2: {1: 20, 5: 20},
         3: {1: 10, 5: 20},
         4: {1: 20, 5: 10},
         5: {2: 20, 3: 20, 4: 10, 6: 10},
         6: {5: 10}
        }

    loss = {1: {2: 0.1, 3: 0.2, 4: 0.4},
         2: {1: 0.1, 5: 0},
         3: {1: 0.2, 5: 0},
         4: {1: 0.4, 5: 0},
         5: {2: 0, 3: 0, 4: 0, 6: 0},
         6: {5: 0}
        }

    # 全局平均时延、丢包
    # 其实total重复算了一次，但是除法抵消
    total_delay = 0
    total_loss = 0
    link_num = 0
    for start in delay.keys():
        for end in delay[start].keys():
            total_delay += delay[start][end]
            total_loss += loss[start][end]
            link_num += 1

    global_delay = total_delay / link_num
    global_loss = total_loss / link_num

    return delay, loss, global_delay, global_loss

# 时延补偿
def dc_calculate(global_delay, delay_require):
    if(delay_require < global_delay):
        dc = pow(global_delay/delay_require, 2)
    else:
        dc = pow(global_delay/delay_require, 0.5)
    return dc;

# 丢包补偿
def lc_calculate(global_loss, loss_require):
    if(loss_require < global_loss):
        lc = pow((1-loss_require)/(1-global_loss), 2)
    else:
        lc = pow((1-loss_require)/(1-global_loss), 0.5)
    return lc;

# 单条链路cost
def cost_i_calculate_QoS(real_delay, dc, real_loss, lc):
    if(real_loss == 1):
        cost_i = float("inf")
    else:
        cost_i = pow(real_delay, dc) * pow(s / (1 - real_loss), lc)
    return cost_i

# 计算源到汇所有路径的代价cost
def cost_calculate_QoS(paths,delay,dc,loss,lc):
    cost = []
    for path in paths:
        cost_i = 0
        for i in range(len(path) - 1):
            cost_i += cost_i_calculate_QoS(delay[path[i]][path[i+1]], dc, loss[path[i]][path[i+1]], lc)
        cost.append(cost_i);
    return cost

def path_QoS(start, end, graph):
    utilization = get_bandwidth()
    paths = findAllPath(graph, start, end)
    paths_copy = paths[:]

    # 拥塞换路
    for path in paths_copy:
        for i in range(len(path) - 1):
            if (utilization[path[i]][path[i + 1]] >= 0.9):
                paths.remove(path)
    if paths == []:
        paths = paths_copy[:]

    delay, loss, global_delay, global_loss = get_data()
    dc = dc_calculate(global_delay, dr)
    lc = lc_calculate(global_loss, lr)
    cost = cost_calculate_QoS(paths, delay, dc, loss, lc)
    interval = weight_calculate(cost)
    path = route(interval, paths)

    return path

# -------------------------------负载均衡模块-------------------------------

# 获取所有主机
def get_all_hosts():
    url = "http://127.0.0.1:8080/v1.0/topology/hosts"
    req = requests.get(url)
    res = req.text
    res = json.loads(res)
    return res

# 获取dpid对应流表
def get_flow(dpid):
    url = "http://127.0.0.1:8080/stats/flow/"+ str(dpid)
    req = requests.get(url)
    res = req.text
    res = json.loads(res)
    return res

# 获取数据流的源和目的
def find_src_dst(src, dst):
    links = get_all_links()
    priority = []
    for link in links:
        if (int(link['src']['dpid'].encode('ascii')) == src and int(link['dst']['dpid'].encode('ascii')) == dst):
            src_port = (int(link['src']['port_no'].encode('ascii')))
            dst_port = (int(link['dst']['port_no'].encode('ascii')))
            flows = get_flow(dst)
            for flow in flows[str(dst)]:
                if flow['match'].get('in_port') and flow['match']['in_port'] == dst_port:
                    priority.append(flow['priority'])
                    min_priority = min(priority)
            for flow in flows[str(dst)]:
                if flow['match'].get('in_port') and flow['match']['in_port'] == dst_port and flow['priority'] == min_priority:
                    return flow['match']['dl_src'].encode('ascii'), flow['match']['dl_dst'].encode('ascii')

# 处理低优先级, 在带宽利用率过高调用, src、dst指一段链路上的源和目的
def low_priority(src, dst, graph):
    # 返回真正的主机源mac和目的mac
    src, dst = find_src_dst(src, dst)
    hosts = get_all_hosts()

    for host in hosts:
        if host['mac'] == src:
            start = int(host['port']['dpid'])
            start_port = int(host['port']['port_no'])
        if host['mac'] == dst:
            end = int(host['port']['dpid'])
            end_port = int(host['port']['port_no'])

    path = path_bandwidth(start, end, graph)
    add_flow(path, start_port, end_port, src, dst)

# -------------------------------流表下发模块模块-------------------------------

# src_port指源主机对应端口
def add_flow(path,start_port,end_port,src_mac,dst_mac):
    links = get_all_links()
    port_list = []
    for i in range(len(path) - 1):
        for link in links:
            if (int(link['src']['dpid'].encode('ascii')) == path[i] and int(link['dst']['dpid'].encode('ascii')) == path[i+1]):
                src_port = (int(link['src']['port_no'].encode('ascii')))
                dst_port = (int(link['dst']['port_no'].encode('ascii')))
                port_list.append(src_port)
                port_list.append(dst_port)
    port_list.insert(0, start_port)
    port_list.append(end_port)

    for i in range(len(path)):
        match = {"in_port": port_list[2*i], "dl_src": str(src_mac), "dl_dst": str(dst_mac)}
        print(match)
        priority = "32768"
        actions = [{"type": "OUTPUT", "port": port_list[2*i+1]}]
        add_flow_entry(path[i], match, priority, actions)

        match = {"in_port": port_list[2 * i + 1], "dl_src": str(dst_mac), "dl_dst": str(src_mac)}
        print(match)
        priority = "32768"
        actions = [{"type": "OUTPUT", "port": port_list[2 * i]}]
        add_flow_entry(path[i], match, priority, actions)

def get_mac(src, dst, src_port, dst_port):
    hosts = get_all_hosts()
    src_mac = ''
    dst_mac = ''
    for host in hosts:
        if int(host['port']['dpid']) == src and int(host['port']['port_no']) == src_port:
            src_mac = host['mac'].encode('ascii')
        if int(host['port']['dpid']) == dst and int(host['port']['port_no']) == dst_port:
            dst_mac = host['mac'].encode('ascii')
    return src_mac,dst_mac

# -------------------------------------------------------------------
# 选路+下发流表
def Routing(graph, src, dst, src_port, dst_port, video):
    if not video:
        path = path_bandwidth(src, dst, graph)
        print(path)
        src_mac, dst_mac = get_mac(src, dst, src_port, dst_port)
        add_flow(path, src_port, dst_port, src_mac, dst_mac)
    else:
        path = path_QoS(src, dst, graph)
        src_mac, dst_mac = get_mac(src, dst, src_port, dst_port)
        add_flow(path, src_port, dst_port, src_mac, dst_mac)

if __name__== "__main__":
    # 全局变量
    graph = get_graph()

    # 丢包敏感度
    s = 1

    # 指定延时要求、丢包要求
    dr = 80
    lr = 0.05

    src = 1
    dst = 5
    src_port = 1
    dst_port = 4
    Routing(graph, src, dst, src_port, dst_port, False)
    Routing(graph, 1, 5, 2, 4, False)