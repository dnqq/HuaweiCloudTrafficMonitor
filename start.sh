#!/bin/bash

# 设置项目目录为脚本所在目录
PROJECT_DIR=$(dirname "$(readlink -f "$0")")
cd "$PROJECT_DIR" || exit

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "创建虚拟环境失败。请确保已安装python3和venv模块。"
        exit 1
    fi
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "正在安装依赖..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "安装依赖失败。"
    deactivate
    exit 1
fi

# 运行主程序
echo "正在运行主程序..."
python main.py

# 退出虚拟环境
deactivate

echo "脚本执行完毕。"