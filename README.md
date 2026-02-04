# 环境准备

## 安装multipass

```shell
chmod +x tools/main.py
ln -s $(pwd)/tools/main.py /usr/local/bin/mpc
```

## 安装代码依赖

# k3s 使用规范

## 命名规范

为了使工具正常工作，虚拟机名称需要包含以下关键词：

* **main节点** ：名称中包含 "main"（不区分大小写）
* **worker节点** ：名称中包含 "worker"（不区分大小写）

例如：

* `k3s_main_01`, `k8s_main_01`
* `k3s_worker-01`, `k8s_worker_02`

# 操作命令

```shell
# 查看所有命令
python tools/main.py --help

# 启动所有虚拟机 (先main后worker)
python tools/main.py start

# 挂起所有虚拟机 (先worker后main)
python tools/main.py suspend

# 关闭所有虚拟机 (先worker后main)
python tools/main.py stop

# 查看状态
python tools/main.py status

# 查看main节点状态
python tools/main.py status --main

# 查看worker节点状态
python tools/main.py status --worker
```
