# 环境准备

## 系统要求
- macOS 或 Linux 系统
- Python 3.8 或更高版本
- Multipass 虚拟机管理工具

## 安装 Multipass

### macOS (使用 Homebrew)
```shell
brew install --cask multipass
multipass version
```

### Linux (Ubuntu/Debian)
```shell
sudo snap install multipass
multipass version
```

## 安装 Python 依赖

### 使用 pip (推荐)
```shell
# 创建虚拟环境 (可选但推荐)
python -m venv venv
source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

### 使用 conda
```shell
# 创建 conda 环境
conda create -n multipass-k3s python=3.8
conda activate multipass-k3s

# 安装依赖包
pip install -r requirements.txt
```

### 手动安装依赖
```shell
pip install click PyYAML
```

## 部署工具

```shell
# 添加执行权限
chmod +x src/main.py

# 创建全局命令链接 (可选)
ln -s $(pwd)/src/main.py /usr/local/bin/mkc

# 验证安装
mkc --help
```

## 验证安装

运行以下命令验证所有组件安装正确：

```shell
# 检查 Multipass
multipass version

# 检查 Python 依赖
python -c "import click, yaml; print('Dependencies installed successfully')"

# 检查工具命令
mkc --help
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

# 配置管理命令
python src/provisioner_v2.py --generate  # 生成配置到 generated/ 目录
python src/provisioner_v2.py --dry-run    # 预览创建命令
python src/provisioner_v2.py              # 实际创建虚拟机

# 使用增强的配置器
python src/provisioner_v2.py --help       # 查看所有选项

# 🆕 新增功能特性

## 配置系统增强

### 通用配置继承机制
项目现在支持强大的配置继承系统：

1. **通用默认配置** (`config/common.yaml`): 包含所有节点的默认设置
2. **节点特定配置** (`config/nodes/`): 可以覆盖通用默认值
3. **智能合并**: 节点配置优先，未指定的设置继承通用默认值

### 配置文件结构

#### config/common.yaml - 通用默认配置
```yaml
# 全局设置
global:
  base_image: "22.04"
  resources:
    cpus: 2
    memory: "2G"
    disk: "10G"

# 节点默认设置 (可被节点配置覆盖)
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

#### config/nodes/k3s-main-01.yaml - 节点特定配置
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

#### config/nodes/k3s-worker-02.yaml - 部分覆盖示例
```yaml
nodes:
  - name: "k3s-worker-02"
    # 只覆盖特定设置
    description: "K3s worker node 02 with custom resources"
    resources:
      memory: "4G"  # 双倍内存
      disk: "15G"   # 额外磁盘空间
    # type, cpus, image, network, mounts 继承自 common.yaml
```

## 增强的配置器功能

### 配置生成
```bash
# 生成所有节点的合并配置到 generated/ 目录
python src/provisioner_v2.py --generate

# 指定输出目录
python src/provisioner_v2.py --generate --output-dir my-configs
```

### 预览模式
```bash
# 预览将要执行的 multipass 命令
python src/provisioner_v2.py --dry-run
```

### 实际创建
```bash
# 使用合并后的配置创建虚拟机
python src/provisioner_v2.py
```

## 模块化架构

项目现在采用模块化设计：

### src/main.py
- CLI 主入口程序
- 调用其他模块功能
- 保持简洁的接口

### src/utils.py
- 通用工具函数
- `run_command`: 执行任意命令
- `get_vm_list`: 获取虚拟机列表
- `load_config`: 加载 YAML 配置

### src/k3s_operator.py
- 节点管理功能
- `start_nodes`: 启动所有节点
- `stop_nodes`: 停止所有节点
- `suspend_nodes`: 挂起所有节点

### src/provisioner_v2.py
- 增强的配置器
- 配置合并功能
- Multipass 集成
- 配置文件生成

## 配置继承示例

以 `k3s-worker-02` 节点为例：
- **继承自 common.yaml**: CPU 2核, 内存 2G, 磁盘 10G, Ubuntu 22.04
- **覆盖配置**: 内存增加到 4G, 磁盘增加到 15G
- **结果**: 使用 2核 CPU, 4G 内存, 15G 磁盘, Ubuntu 22.04

## 优势

1. **减少重复**: 通用设置集中管理，避免每个节点重复定义
2. **灵活覆盖**: 节点可以完全继承、部分覆盖或完全自定义配置
3. **易于维护**: 修改通用设置只需更新一个文件
4. **清晰注释**: 每个配置文件都包含注释说明继承和覆盖关系
5. **模块化设计**: 代码结构清晰，易于扩展和维护

## 快速开始

1. **编辑通用配置**: 修改 `config/common.yaml` 设置默认值
2. **配置特定节点**: 在 `config/nodes/` 目录中创建节点配置文件
3. **生成配置**: `python src/provisioner_v2.py --generate`
4. **预览命令**: `python src/provisioner_v2.py --dry-run`
5. **创建虚拟机**: `python src/provisioner_v2.py`
6. **管理节点**: 使用 `mkc start|stop|status` 命令

这个新的配置系统让您能够轻松管理复杂的多节点环境，同时保持配置的简洁性和一致性。
```
