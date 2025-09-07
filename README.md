# Huawei Cloud Flexus L Instance Traffic Monitor

本程序专门用于监控华为云 **Flexus L** 实例的免费流量，并在流量低于预设阈值时通过 Telegram 发送告警。

## 功能

- 定期查询华为云免费资源的流量使用情况。
- 设置三级流量阈值，对应不同的告警级别。
- 流量过低时自动触发关机程序（可选）。
- 通过 Telegram Bot 发送实时通知。
- 支持调试模式，方便测试。

## 如何使用

1.  **克隆或下载项目**
    将项目代码下载到您需要监控的服务器上。

    > **说明**
    > 关机功能默认通过 `sudo shutdown` 命令实现。华为云官方也提供了关机 API，如果您有兴趣，可以自行研究并修改 `main.py` 中的 `shutdown_server` 函数以实现更优雅的关机方式。

2.  **配置环境变量**
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

3.  **运行程序**
    执行 `start.sh` 脚本来启动监控程序：
    ```bash
    bash start.sh
    ```

4.  **（推荐）使用 Cron 定时执行**
    为了实现自动化监控，您可以设置一个 `cron` 定时任务来定期运行此脚本。例如，每小时执行一次。

    首先，打开您的 crontab 编辑器：
    ```bash
    crontab -e
    ```

    然后，在文件末尾添加以下行。请确保将 `/path/to/your/project` 替换为 `start.sh` 脚本所在的绝对路径。
    ```cron
    0 * * * * /bin/bash /path/to/your/project/start.sh
    ```
    这行配置的含义是，在每小时的第 0 分钟，执行 `start.sh` 脚本。

## 注意事项

- 关机功能默认在 Linux 系统下使用 `sudo shutdown -h now`。如果您的系统不同，请修改 `main.py` 中的 `shutdown_server` 函数。
- 脚本会在临时目录创建一个 `huaweicloud_traffic_state.json` 文件来保存上次运行和通知的状态，请勿删除。
