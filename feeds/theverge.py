import logging
from feeds.base import FeedBase

logger = logging.getLogger(__name__)


# class ThevergeFeed(FeedBase):
#     url = "https://www.theverge.com/rss/index.xml"
#     interval = 60

#     def fetch_data(self):
#         data = super().fetch_data()
#         self.logger.info("Fetched data from ThevergeFeed")
#         return data
