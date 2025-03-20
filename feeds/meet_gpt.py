from feeds.base import Article, FeedBase
import xml.etree.ElementTree as ET
from dateutil import parser

from feeds.telegram_channel_bot import TelegramChannelFeedBase


class MeetGPTTelegramFeed(TelegramChannelFeedBase):
    """
    订阅 风向旗参考快讯 的 Telegram 频道
    """

    channel_name = "meet_chatgpt"
    interval = 30

    def __init__(self):
        super().__init__(self.channel_name)
