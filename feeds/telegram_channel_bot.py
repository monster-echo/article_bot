from feeds.base import Article, FeedBase
from dateutil import parser
import xml.etree.ElementTree as ET


class TelegramChannelFeedBase(FeedBase):
    channel_name = ""

    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.url = f"https://rsshub.0x2a.top/telegram/channel/{channel_name}"
        super().__init__()

    def parse_articles(self, response_text):
        """
        解析 RSS 源中的文章
        """

        root = ET.fromstring(response_text)
        channel = root.find("channel")
        title = channel.find("title").text
        link = channel.find("link").text
        description = channel.find("description").text

        self.logger.info(f"频道标题: {title}")
        self.logger.info(f"频道链接: {link}")
        self.logger.info(f"频道描述: {description}")
        self.logger.info(f"频道文章数量: {len(channel.findall('item'))}")
        self.logger.info(
            f"频道更新时间: {parser.parse(channel.find('lastBuildDate').text)}"
        )

        articles = []
        for entry in channel.findall("item"):
            try:
                articles.append(
                    Article(
                        title=entry.findtext("title", default=""),
                        link=entry.find("link").text,
                        article_id=entry.find("guid").text,
                        published=parser.parse(entry.find("pubDate").text),
                        author=entry.findtext("author", default=""),
                        description=entry.findtext("description", ""),
                        categories=[c.text for c in entry.findall("category")],
                        source=f"{self.channel_name}-Telegram",
                    )
                )
            except Exception as e:
                self.logger.error(f"解析条目失败: {str(e)}")
                continue

        return articles
