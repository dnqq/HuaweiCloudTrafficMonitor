# Huawei Cloud Flexus L Instance Traffic Monitor

本程序专门用于监控华为云 **Flexus L** 实例的免费流量，并在流量低于预设阈值时通过 Telegram 发送告警。

## 功能

- 定期查询华为云免费资源的流量使用情况。
- 设置三级流量阈值，对应不同的告警级别。
- 流量过低时自动触发关机程序（可选）。
- 通过 Telegram Bot 发送实时通知。
- 支持调试模式，方便测试。

## 如何使用

1.  **环境准备**
    - **安装Python**: 确保您的服务器上已安装 Python 3。
    - **安装venv模块**: 本项目依赖 Python 的虚拟环境。在某些系统（如 Debian/Ubuntu）上，`venv` 模块需要单独安装。如果 `start.sh` 脚本在创建虚拟环境时失败，并提示 `ensurepip is not available`，请根据您的 Python 版本执行相应的安装命令。例如：
      ```bash
      sudo apt update
      sudo apt install python3-venv
      ```
      这个命令通常会自动为您的系统默认的 Python 3 版本安装 `venv` 支持。如果您的系统上有多个 Python 版本，或者此命令无效，您可能需要根据 `python3 --version` 的输出来安装一个特定版本的包（例如 `python3.11-venv`）。

2.  **克隆或下载项目**
    将项目代码下载到您需要监控的服务器上。

    > **说明**
    > 关机功能默认通过 `sudo shutdown` 命令实现。华为云官方也提供了关机 API，如果您有兴趣，可以自行研究并修改 `main.py` 中的 `shutdown_server` 函数以实现更优雅的关机方式。

3.  **配置环境变量**
    复制 `.env.example` 文件为 `.env`，并填入您的配置信息：
    - `HUAWEICLOUD_SDK_AK` & `HUAWEICLOUD_SDK_SK`: 您的华为云 Access Key ID 和 Secret Access Key。
        - **重要**: 您使用的 Access Key 需要拥有 **BSS ReadonlyAccess** 权限。
        - 获取方法请参考官方文档：[如何获取AK/SK](https://support.huaweicloud.com/devg-apisign/api-sign-provide.html)
    - `FREE_RESOURCE_IDS`: 您要监控的免费资源ID。
        - 获取方法：访问华为云API Explorer中的 `ListAllResources` 接口([直达链接](https://console.huaweicloud.com/apiexplorer/#/openapi/Config/debug?api=ListAllResources))。在响应结果中，找到 `logical_resource_type` 为 `"huaweicloudinternal_cbc_freeresource"` 的条目，其对应的 `physical_resource_id` 即为您需要的ID。
    - `TELEGRAM_BOT_TOKEN`: 您的 Telegram Bot Token。
    - `TELEGRAM_CHAT_ID`: 您的 Telegram Chat ID。
    - `SERVER_NAME`: 您的服务器名称（例如：华为新加坡）。
    - `THRESHOLD_LEVEL_1`: 关机阈值 (GB)。
    - `THRESHOLD_LEVEL_2`: 高频告警阈值 (GB)。
    - `THRESHOLD_LEVEL_3`: 普通告警阈值 (GB)。

4.  **首次运行与测试**
    在配置自动任务之前，请先手动执行一次 `start.sh` 脚本。这将完成创建Python虚拟环境、安装所需依赖等初始化工作。
    ```bash
    bash start.sh
    ```
    观察脚本输出，确保程序能够无误地运行并发送测试通知（如果流量低于阈值）。

5.  **（推荐）配置 Cron 定时执行**
    在手动测试成功后，为了实现自动化监控，您可以设置一个 `cron` 定时任务来定期运行此脚本。

    首先，打开您的 crontab 编辑器：
    ```bash
    crontab -e
    ```

    然后，在文件末尾添加以下行。请确保将 `/path/to/your/project` 替换为 `start.sh` 脚本所在的 **绝对路径**。例如，每小时执行一次：
    ```cron
    0 * * * * /bin/bash /path/to/your/project/start.sh >/dev/null 2>&1
    ```
    - `0 * * * *` 表示在每小时的第0分钟执行。
    - `>/dev/null 2>&1` 会将脚本的所有输出（标准输出和错误输出）重定向到“黑洞”，避免 `cron` 发送不必要的邮件通知。

## 故障排查

- **错误: `venv/bin/activate: No such file or directory`**
  - **原因**: 这个问题通常是因为上一次创建虚拟环境失败，但留下了一个不完整的 `venv` 目录。当 `start.sh` 再次运行时，它检测到 `venv` 目录存在，便跳过了创建步骤，直接尝试激活一个不存在的文件，从而导致错误。
  - **解决方法**:
    1.  手动删除损坏的虚拟环境目录：`rm -rf venv`
    2.  重新运行脚本：`bash start.sh`
  - **预防**: 最新版的 `start.sh` 脚本已包含修复逻辑，在创建虚拟环境失败时会自动清理残留目录，以防止此问题再次发生。

## 注意事项

- 关机功能默认在 Linux 系统下使用 `sudo shutdown -h now`。如果您的系统不同，请修改 `main.py` 中的 `shutdown_server` 函数。
- 脚本会在临时目录创建一个 `huaweicloud_traffic_state.json` 文件来保存上次运行和通知的状态，请勿删除。
