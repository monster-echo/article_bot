from bots.base import BotBase
import json
import re


class GodlyNewsBot(BotBase):
    interval = 60 * 60  # 每小时执行一次
    file_prefix = "GodlyNews1-Telegram-"
    output_folder = "GodlyNews1"
    output_prefix = "GodlyNews1"
    min_files_required = 3

    def extract_tags(self, text):
        """提取文本中的标签"""
        if not text:
            return []

        tags = []
        # 查找所有 #标签 格式的内容
        tag_pattern = r"#(\w+)"
        found_tags = re.findall(tag_pattern, text)
        if found_tags:
            tags.extend(found_tags)

        return tags

    def generate_title_prompt(self, article_content):
        """生成新闻文章标题的提示词"""
        return f"""
        你现在是一个新闻文章公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个吸引人的、能够引起用户兴趣的新闻文章标题。标题应当突出新闻价值，吸引用户点击查看。
        """

    def generate_article_prompt(self, articles_info):
        """生成新闻文章的提示词"""
        return f"""
        你现在是一个新闻文章公众号编辑，需要根据以下几篇文章的信息整合生成一篇新闻公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于最新新闻信息的公众号文章，要求：
        1. 按新闻类型进行分类（如时事新闻、科技新闻、财经新闻等）
        2. 每个新闻介绍要简洁明了，突出其核心价值和使用方法
        3. 提供清晰的参与步骤或领取方式
        4. 保留原文中的重要链接和入口信息
        5. 适当添加一些使用建议或领取技巧
        6. 注明活动时间和有效期（如果有提供）
        7. 文末可以总结本次优惠信息的特点或提供使用建议
        
        生成一篇实用性强、能帮助读者获取新闻的优质文章。
        """
