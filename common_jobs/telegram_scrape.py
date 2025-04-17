from datetime import datetime, timedelta
import json
import os
import tempfile
import requests
from telethon import TelegramClient
from common_jobs.base import CommonJobBase
from telethon.tl.types import PeerChannel
from config import AISTUDIOX_API_URL
from utils.appdata import app_data


# 保存和加载last_message_id的文件路径
LAST_MESSAGES_FILE = app_data.get_file_path("telegram_scrape/last_messages.json")


class TelegramScrapeJob(CommonJobBase):

    interval = 60 * 5  # 5 minutes

    def __init__(self):
        super().__init__()
        self.last_messages = self.load_last_messages()
        self.db = app_data.get_file_path("telegram_scrape/session.session")

    async def addNewMessage(self, message):
        url = f"{AISTUDIOX_API_URL}/api/drafts"

        source = message["source"]
        # 直接使用字典作为form data
        form_data = {
            "title": message["title"],
            "content": message["content"],
            "source": source,
            "author": message["author"],
            "published": message["published"],
            "link": message["link"],
        }

        files = [
            (
                "files",
                (os.path.basename(file), open(file, "rb"), "application/octet-stream"),
            )
            for file in message["media_files"]
            if file
        ]

        response = requests.post(url, data=form_data, files=files)
        response.raise_for_status()
        self.logger.info(f"添加消息成功: {source}")

    async def sync_channel(self, client, channel):
        channel_entity = await client.get_entity(
            PeerChannel(int(channel)) if channel < 0 else channel
        )

        grouped_messages = []
        # 加载上次处理的消息ID
        channel_key = str(channel)
        last_message_id = self.last_messages.get(channel_key, 0)
        self.logger.info(
            f"从频道 {channel} 获取消息，上次处理到消息ID: {last_message_id}"
        )

        # 获取频道消息
        async for message in client.iter_messages(
            channel_entity,
            limit=11,
            offset_id=last_message_id,
            # 过去7天内
            offset_date=datetime.now() - timedelta(days=7),
            reverse=True if last_message_id else False,
        ):
            if message.id > last_message_id:
                last_message_id = message.id

            self.logger.info(f"获取 {channel} 消息: {message.id} - {message.text}")
            file_path = await message.download_media(tempfile.gettempdir())
            self.logger.info(f"Downloaded media for message {message.id} {file_path}")
            channel_username = (
                channel_entity.usernames[0]
                if channel_entity.usernames
                else channel_entity.username
            )

            # 查找是否存在相同 grouped_id 的消息
            found_message = (
                next(
                    (
                        m
                        for m in grouped_messages
                        if m["groupedId"] == message.grouped_id
                    ),
                    None,
                )
                if message.grouped_id
                else None
            )
            if found_message:
                # 如果消息已经存在于分组中，则添加媒体文件
                self.logger.info(f"消息 {message.id} 已存在于分组消息中.")
                if message.text:
                    found_message["content"] = message.text
                found_message["media_files"].append(file_path)
            else:
                self.logger.info(f"消息 {message.id} 不在分组消息中，创建新的分组.")
                grouped_messages.append(
                    {
                        "title": "",
                        "content": message.text,
                        "source": channel_entity.title,
                        "author": channel_username,
                        "published": message.date.isoformat(),
                        "link": f"https://t.me/c/{channel_entity.id}/{message.id}",
                        "groupedId": message.grouped_id,
                        "media_files": [file_path],
                    }
                )

        # 处理完成后更新并保存最后的消息ID
        self.last_messages[channel_key] = last_message_id
        self.save_last_messages(self.last_messages)
        self.logger.info(f"已更新频道 {channel} 的最后消息ID为 {last_message_id}")

        for message in grouped_messages:
            self.logger.info(f"正在处理分组消息 {message['groupedId']}")
            await self.addNewMessage(message)

        self.logger.info(f"同步 {channel} 完成，处理了 {len(grouped_messages)} 条消息")

    async def sync_channels(self, client):
        channels = [
            int(channel.strip())
            for channel in (os.environ.get("SCRAPE_CHANNELS", "").split(","))
            if channel.strip()
        ]

        if not channels:
            raise Exception("请设置 SCRAPE_CHANNELS 环境变量")

        for channel in channels:
            try:
                self.logger.info(f"开始同步频道: {channel}")
                await self.sync_channel(client, channel)
                self.logger.info(f"同步频道成功: {channel}")
            except Exception as e:
                self.logger.error(f"同步频道失败: {channel} - {e}")
                continue

    async def start(self):
        async with TelegramClient(
            self.db,
            os.environ.get("TELEGRAM_API_ID"),
            os.environ.get("TELEGRAM_API_HASH"),
        ) as client:
            self.logger.info("开始同步 Telegram 频道")
            client.start()
            self.logger.info("同步 Telegram 频道成功")

    async def run(self):
        if not os.path.exists(self.db):
            raise Exception("请先登录 Telegram")

        try:
            async with TelegramClient(
                self.db,
                os.environ.get("TELEGRAM_API_ID"),
                os.environ.get("TELEGRAM_API_HASH"),
            ) as client:

                self.logger.info("开始同步 Telegram 频道")
                await self.sync_channels(client)
                self.logger.info("同步 Telegram 频道成功")
        except Exception as e:
            self.logger.error(f"同步 Telegram 失败: {e}")

    def load_last_messages(self):
        """从JSON文件加载每个频道的最后处理的消息ID"""
        if not os.path.exists(LAST_MESSAGES_FILE):
            return {}

        try:
            with open(LAST_MESSAGES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载last_messages文件失败: {e}")
            return {}

    def save_last_messages(self, last_messages):
        """保存每个频道的最后处理的消息ID到JSON文件"""
        try:
            with open(LAST_MESSAGES_FILE, "w") as f:
                json.dump(last_messages, f)
            self.logger.info("已保存last_messages")
        except Exception as e:
            self.logger.error(f"保存last_messages文件失败: {e}")
            raise e
