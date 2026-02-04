# 环境准备

工具是在mac上安装，需要环境中提前安装python3运行环境。

## 安装multipass

```shell
brew cask install multipass
multipass -v
```

## 部署环境

```shell

chmod +x src/main.py
ln -s $(pwd)/src/main.py /usr/local/bin/mkc
```

# k3s 使用规范

## 命名规范

为了使工具正常工作，虚拟机名称需要包含以下关键词：

* **main节点** ：名称中包含 "main"（不区分大小写）
* **worker节点** ：名称中包含 "worker"（不区分大小写）

例如：

* `k3s_main_01`, `k8s_main_01`
* `k3s_worker_01`, `k8s_worker_02`

# 操作命令

```shell
# 查看所有命令
mkc --help

# 启动所有虚拟机 (先main后worker)
mkc start

# 挂起所有虚拟机 (先worker后main)
mkc suspend

# 关闭所有虚拟机 (先worker后main)
mkc shutdown

# 查看状态
mkc status

# 查看main节点状态
mkc status --main

# 查看worker节点状态
mkc status --worker
```
