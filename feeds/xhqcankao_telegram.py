from feeds.telegram_channel_bot import TelegramChannelFeedBase


class XhqCanKaoTelegramFeed(TelegramChannelFeedBase):
    """
    订阅 风向旗参考快讯 的 Telegram 频道
    """

    channel_name = "xhqcankao"
    interval = 30

    def __init__(self):
        super().__init__(self.channel_name)
