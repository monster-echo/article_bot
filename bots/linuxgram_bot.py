from bots.base import BotBase
import json
import os
from datetime import datetime
import re
from bs4 import BeautifulSoup


class LinuxgramBot(BotBase):
    file_prefix = "linuxgram-"
    output_folder = "linuxgram"
    output_prefix = "linuxgram"
    interval = 60 * 60  # 每小时执行一次

    def generate_title_prompt(self, article_content):
        """生成Linux文章标题的提示词"""
        return f"""
        你现在是一个Linux技术内容公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个技术性强、吸引人的Linux相关公众号文章标题。
        """

    def generate_article_prompt(self, articles_info):
        """生成Linux文章的提示词"""
        return f"""
        你现在是一个Linux技术内容公众号编辑，需要根据以下几篇文章的信息整合生成一篇技术干货公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于Linux技术的公众号文章，要求：
        1. 保持技术内容的准确性和专业性
        2. 结构清晰，分段合理，可以适当添加小标题
        3. 提炼核心技术要点，解释复杂概念
        4. 增加一些个人见解和实用建议
        5. 文末可以添加简短总结
        6. 保留原文中的重要链接
        
        生成高质量的Linux技术文章。
        """
