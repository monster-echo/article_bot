from feeds.base import Article, FeedBase
import xml.etree.ElementTree as ET
from dateutil import parser


class ThoughtcoFeed(FeedBase):
    url = "https://rsshub.0x2a.top/thoughtco/computer-science-4133486"
    interval = 60  # 可以针对每个 feed 设置不同的抓取间隔

    def parse_articles(self, response_text):
        root = ET.fromstring(response_text)
        # 使用新模型处理数据
        articles = []
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

        for entry in channel.findall("item"):
            try:
                articles.append(
                    Article(
                        title=entry.find("title").text,
                        link=entry.find("link").text,
                        article_id=entry.find("guid").text,
                        published=parser.parse(entry.find("pubDate").text),
                        author=entry.find("author").text,
                        description=entry.find("description").text,
                        categories=[c.text for c in entry.findall("category")],
                        source="Thoughtco",
                    )
                )
            except Exception as e:
                self.logger.error(f"Failed to parse entry: {str(e)}")
                continue
        return articles
