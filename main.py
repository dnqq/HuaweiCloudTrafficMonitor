#
# Copyright (c) Huawei Technologies CO., Ltd. 2022-2025. All rights reserved.
#
# coding=utf-8
import os
import requests
import json
import subprocess
import tempfile
import sys
import time
from dotenv import load_dotenv
from apig_sdk import signer

def send_telegram_message(message):
    """发送消息到Telegram用户或群组。"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print("Telegram的bot_token或chat_id未配置。")
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram通知已发送。")
        return True
    except requests.exceptions.RequestException as e:
        print(f"发送Telegram通知失败: {e}")
        return False

def shutdown_server(server_name, amount, original_amount, start_time, end_time, usage_type_name):
    """执行服务器关机。"""
    print("关机程序启动...")
    # 发送10次告警
    for i in range(10):
        print(f"发送第 {i+1}/10 次关机告警...")
        message = (
            f"‼️ *紧急警告* ‼️\n"
            f"服务器: *{server_name}*\n"
            f"剩余流量: *{amount:.2f} GB*，极低！服务器即将关闭！\n"
            f"套餐总流量: *{original_amount:.2f} GB*\n"
            f"流量类型: *{usage_type_name}*\n"
            f"统计周期: {start_time[:10]} to {end_time[:10]}\n"
            f"(告警 {i+1}/10)"
        )
        send_telegram_message(message)
        time.sleep(5) # 每次发送后等待5秒

    print("发送最终关机通知...")
    send_telegram_message(f"服务器 *{server_name}* 正在关闭。")
    
    # 适用于Linux系统。如果使用的是Windows，请使用 'shutdown /s /t 1'。
    if sys.platform == "linux":
        print("执行Linux关机命令。")
        subprocess.run(["sudo", "shutdown", "-h", "now"])
    else:
        print("检测到非Linux系统，跳过关机命令。")

def get_state(file_path):
    """从文件加载状态 (上次运行/通知时间)。"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_state(file_path, state):
    """保存状态到文件。"""
    with open(file_path, 'w') as f:
        json.dump(state, f)

if __name__ == '__main__':
    load_dotenv()

    # --- 加载配置 ---
    AK = os.getenv('HUAWEICLOUD_SDK_AK')
    SK = os.getenv('HUAWEICLOUD_SDK_SK')
    RESOURCE_IDS = os.getenv('FREE_RESOURCE_IDS')
    SERVER_NAME = os.getenv('SERVER_NAME', '默认服务器')
    
    # 阈值配置
    T1 = float(os.getenv('THRESHOLD_LEVEL_1', 200))
    T2 = float(os.getenv('THRESHOLD_LEVEL_2', 300))
    T3 = float(os.getenv('THRESHOLD_LEVEL_3', 500))

    # 调试模式
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() in ('true', '1', 't')
    
    if not all([AK, SK, RESOURCE_IDS]):
        print("缺少必要的环境变量: HUAWEICLOUD_SDK_AK, HUAWEICLOUD_SDK_SK, FREE_RESOURCE_IDS")
        exit(1)

    # --- 初始化签名 ---
    sig = signer.Signer()
    sig.Key = AK
    sig.Secret = SK

    # --- 构建API请求 ---
    method = "POST"
    url = "https://bss.myhuaweicloud.com/v2/payments/free-resources/usages/details/query"
    headers = {'host': 'bss.myhuaweicloud.com', "Content-Type": "application/json"}
    body = json.dumps({"free_resource_ids": RESOURCE_IDS.split(',')})

    r = signer.HttpRequest(method, url, headers, body)
    sig.Sign(r)

    try:
        # --- 发送API请求 ---
        resp = requests.request(method, url, headers=r.headers, data=body)
        resp.raise_for_status()

        print(f"状态码: {resp.status_code}")
        data = resp.json()
        print(f"API响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        free_resources = data.get("free_resources", [])
        if not free_resources:
            print("API响应中未找到免费资源信息。")
            exit()
            
        # --- 状态文件处理 ---
        temp_dir = tempfile.gettempdir()
        state_file = os.path.join(temp_dir, "huaweicloud_traffic_state.json")
        state = get_state(state_file)
        now = time.time()
        
        last_run_time = state.get('last_run_time', 0)
        last_notify_time = state.get('last_notify_time', 0)

        # --- 核心逻辑 ---
        for resource in free_resources:
            amount = resource.get("amount", 0)
            original_amount = resource.get("original_amount", 0)
            start_time = resource.get("start_time", "N/A")
            end_time = resource.get("end_time", "N/A")
            usage_type_name = resource.get("usage_type_name", "N/A")
            print(f"资源ID: {resource.get('free_resource_id')}, 剩余流量: {amount} GB, 套餐总量: {original_amount} GB")

            # 等级1: 关机
            if amount < T1:
                print(f"流量低于阈值1 ({T1}GB)，启动关机程序。")
                shutdown_server(SERVER_NAME, amount, original_amount, start_time, end_time, usage_type_name)
                break # 关机后无需继续处理
            
            # 等级2: 频繁告警
            elif amount < T2:
                print(f"流量低于阈值2 ({T2}GB)，每小时检查并告警。")
                if not DEBUG_MODE and now - last_run_time < 3600: # 1小时
                    print("距离上次运行不足1小时，跳过。")
                    continue
                message = (f"🟠 *中级警告* 🟠\n"
                           f"服务器: *{SERVER_NAME}*\n"
                           f"剩余流量为 *{amount:.2f} GB*，已低于 {T2} GB。\n"
                           f"套餐总流量: *{original_amount:.2f} GB*\n"
                           f"流量类型: *{usage_type_name}*\n"
                           f"统计周期: {start_time[:10]} to {end_time[:10]}")
                send_telegram_message(message)
                state['last_run_time'] = now
                state['last_notify_time'] = now

            # 等级3: 普通告警
            elif amount < T3:
                print(f"流量低于阈值3 ({T3}GB)，每4小时检查，每24小时告警。")
                if not DEBUG_MODE and now - last_run_time < 4 * 3600: # 4小时
                    print("距离上次运行不足4小时，跳过。")
                    continue
                
                state['last_run_time'] = now # 记录运行时间
                if DEBUG_MODE or now - last_notify_time > 24 * 3600: # 24小时
                    message = (f"🟡 *低级警告* 🟡\n"
                               f"服务器: *{SERVER_NAME}*\n"
                               f"剩余流量为 *{amount:.2f} GB*，已低于 {T3} GB。\n"
                               f"套餐总流量: *{original_amount:.2f} GB*\n"
                               f"流量类型: *{usage_type_name}*\n"
                               f"统计周期: {start_time[:10]} to {end_time[:10]}")
                    send_telegram_message(message)
                    state['last_notify_time'] = now # 记录通知时间
                else:
                    print("距离上次通知不足24小时，本次不发送通知。")

            # 等级0: 流量充足
            else:
                print("流量充足。")
                if not DEBUG_MODE and now - last_run_time < 4 * 3600:
                    print("距离上次运行不足4小时，跳过。")
                    continue

                state['last_run_time'] = now
                if DEBUG_MODE or now - last_notify_time > 24 * 3600:
                    message = (f"🟢 *流量报告* 🟢\n"
                               f"服务器: *{SERVER_NAME}*\n"
                               f"当前剩余流量为 *{amount:.2f} GB*。\n"
                               f"套餐总流量: *{original_amount:.2f} GB*\n"
                               f"流量类型: *{usage_type_name}*\n"
                               f"统计周期: {start_time[:10]} to {end_time[:10]}")
                    send_telegram_message(message)
                    state['last_notify_time'] = now
                else:
                    print("距离上次通知不足24小时，本次不发送通知。")
        
        # --- 保存状态 ---
        save_state(state_file, state)
        print("脚本执行完毕。")

    except requests.exceptions.RequestException as e:
        print(f"请求过程中发生错误: {e}")
    except json.JSONDecodeError:
        print(f"解析API响应的JSON时失败: {resp.text}")
