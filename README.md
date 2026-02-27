## 项目简介

`multipass_k3s_cli` 是一个基于 Multipass 的轻量级 Kubernetes/k3s 集群管理工具，通过命令行一键完成虚拟机创建、集群启动/挂起/停止等操作，并提供灵活的 YAML 配置继承机制，方便管理多节点环境。

---

## 环境准备

### 系统要求

- **操作系统**: macOS 或 Linux
- **Python**: 3.8 或更高版本
- **虚拟化工具**: Multipass

### 安装 Multipass

#### macOS（Homebrew）

```shell
brew install --cask multipass
multipass version
```

#### Linux（Ubuntu / Debian）

```shell
sudo snap install multipass
multipass version
```

### 安装 Python 依赖

#### 使用 pip（推荐）

```shell
# 创建虚拟环境（可选但推荐）
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 使用 conda

```shell
# 创建 conda 环境
conda create -n multipass-k3s python=3.8
conda activate multipass-k3s

# 安装依赖
pip install -r requirements.txt
```

#### 手动安装核心依赖

```shell
pip install click PyYAML
```

### 安装 CLI 工具

```shell
# 添加执行权限
chmod +x mkc

# 创建全局命令链接（可选）
sudo ln -s "$(pwd)/mkc" /usr/local/bin/mkc

# 验证命令
mkc --help
```

### 安装自检

```shell
# 检查 Multipass
multipass version

# 检查 Python 依赖
python -c "import click, yaml; print('Dependencies installed successfully')"

# 检查 CLI 命令
mkc --help
```

---

## 基本概念与命名规范

为了使工具正常识别节点角色，虚拟机名称需要包含特定关键词（当前版本逻辑如下，后续可与 YAML 配置进一步对齐）：

- **controller 节点**：名称中包含 `main`（TODO：与 controller YAML 中的节点定义保持一致）
- **worker 节点**：名称中包含 `worker`（TODO：与 worker YAML 中的节点定义保持一致）

示例命名：

- `k3s_main_01`, `k8s_main_01`
- `k3s_worker_01`, `k8s_worker_02`

---

## 常用命令

```shell
# 查看所有命令
mkc --help

# 启动 Kubernetes 集群（k3s）
mkc start --cluster-type k3s

# 挂起 Kubernetes 集群
mkc suspend --cluster-type k3s

# 停止 Kubernetes 集群
mkc stop --cluster-type k3s

# 查看虚拟机/节点状态
mkc status

# 初始化虚拟机配置
mkc init --help
mkc init --dry-run   # 预览将要执行的创建命令
mkc init --generate  # 生成配置到 generated/ 目录
mkc init             # 实际创建虚拟机
```

---

## 配置系统与继承机制

### 配置继承概览

项目提供了一套分层的配置系统，便于在多节点环境中复用和覆盖配置：

1. **通用默认配置**：`config/common.yaml`，包含所有节点的全局默认值  
2. **节点特定配置**：`config/nodes/*.yaml`，按节点名覆盖默认配置  
3. **智能合并**：节点配置优先，未指定字段自动继承默认值

### 配置文件结构示例

#### `config/common.yaml`（通用默认配置）

```yaml
# 全局设置
global:
  base_image: "22.04"
  resources:
    cpus: 2
    memory: "2G"
    disk: "10G"

# 节点默认设置（可被节点配置覆盖）
node_defaults:
  type: "worker"
  description: "K3s node"
  resources:
    cpus: 2
    memory: "2G"
    disk: "10G"
  network:
    bridged: false
  mounts: []
  image: "22.04"

# 节点清单
inventory:
  - k3s-main-01: "nodes/k3s-main-01.yaml"
  - k3s-worker-01: "nodes/k3s-worker-01.yaml"
  - k3s-worker-02: "nodes/k3s-worker-02.yaml"
```

#### `config/nodes/k3s-main-01.yaml`（controller 节点）

```yaml
nodes:
  - name: "k3s-main-01"
    # 覆盖通用默认值
    type: "controller"
    description: "K3s main controller node 01"
    resources:
      memory: "4G"  # 更多内存
      disk: "20G"   # 更多磁盘空间
    # 其他设置继承自 common.yaml
```

#### `config/nodes/k3s-worker-02.yaml`（部分覆盖示例）

```yaml
nodes:
  - name: "k3s-worker-02"
    # 只覆盖部分资源
    description: "K3s worker node 02 with custom resources"
    resources:
      memory: "4G"  # 双倍内存
      disk: "15G"   # 额外磁盘空间
    # type, cpus, image, network, mounts 等继承自 common.yaml
```

### 配置继承示例说明

以 `k3s-worker-02` 为例，合并后的最终配置为：

- **继承自 `common.yaml`**：CPU 2 核，内存 2G，磁盘 10G，Ubuntu 22.04，网络/挂载等通用设置  
- **节点覆盖部分**：内存调整为 4G，磁盘调整为 15G，描述信息单独定义  
- **最终结果**：CPU 2 核，内存 4G，磁盘 15G，Ubuntu 22.04

这一机制在不重复配置的前提下，允许你为单个节点做精细化调整。

---

## 代码结构与模块说明

项目采用模块化、面向对象的设计，主要模块包括：

- **`src/main.py`**：CLI 入口，仅负责定义 Click 命令行接口，并调用下层操作器模块  
- **`src/utils.py`**：通用工具函数  
  - `run_command`：执行系统命令  
  - `load_config`：加载 YAML 配置  
  - `deep_merge`：深度字典合并  
  - `file_exists`：文件存在性检查  
- **`src/node_operator.py`**：节点操作（当前基于 Multipass）  
  - `create_node` / `delete_node`：创建/删除虚拟机节点  
  - `get_node_info` / `get_node_status`：获取/检查节点状态  
  - `execute_on_node`：在节点上执行命令  
- **`src/cluster_operator.py`**：集群操作（目前主要支持 k3s）  
  - `start_cluster`：启动集群  
  - `suspend_cluster`：挂起集群  
  - `stop_cluster`：停止集群  
- **`model/node.py`**：`Node` 数据类  
  - 负责单节点配置继承、合并与状态管理  
- **`model/cluster.py`**：`Cluster` 数据类  
  - 负责集群层面的资源汇总、节点清单与状态监控

---

## 快速开始（推荐流程）

1. **准备环境**：安装 Multipass 与 Python 依赖，确保 `mkc` 可用  
2. **编辑通用配置**：修改 `config/common.yaml` 以符合你的默认资源与镜像需求  
3. **定义节点配置**：在 `config/nodes/` 中为各节点创建 YAML 文件  
4. **生成并预览命令**：  
   - 生成命令：`python src/provisioner_v2.py --generate`  
   - 预览执行：`python src/provisioner_v2.py --dry-run`  
5. **创建虚拟机**：`python src/provisioner_v2.py`  
6. **管理集群**：通过 `mkc start|stop|suspend|status` 等命令进行日常运维

---

## 设计优势总结

- **减少重复**：通用配置集中管理，避免在每个节点上重复定义相同字段  
- **灵活覆盖**：节点级别可以选择完全继承、部分覆盖或完全自定义  
- **易于维护**：修改默认行为只需改动一处配置文件  
- **模块化代码结构**：各层职责清晰，方便后续扩展更多集群类型或后端驱动（例如其他虚拟化/云厂商）  
- **适合本地实验与学习**：非常适合在本地快速搭建 k3s/k8s 实验环境

