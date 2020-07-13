## 使用说明

启动mininet并指定控制器后，使用以下命令：

```shell
$ sudo ryu-manager ofctl_rest.py rest_topology.py simple_switch_13.py --observe-links
```

将Routing.py放在与控制器py文件相同文件夹下，在控制器中写入：

```python
import Routing
```

在收到PacketIn报文后解析出：源dpid+目的dpid+源port+目的port，调用以下函数即可完成选路和流表下发：

```python
Routing(src, dst, src_port, dst_port, video)
```

需要指定一下全局变量

```python
# -*- coding: UTF-8 -*-
from Routing import *

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
```