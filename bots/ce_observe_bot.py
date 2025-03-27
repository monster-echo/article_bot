from bots.base import BotBase


class CEObserveBot(BotBase):
    file_prefix = "CE_Observe-Telegram-"
    output_folder = "tech_news"
    output_prefix = "tech_news"

    def generate_title_prompt(self, article_content):
        """生成科技文章标题的提示词"""
        return f"""
        你现在是一个科技资讯公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个科技感强、吸引人的公众号文章标题。
        """

    def generate_article_prompt(self, articles_info):
        """生成科技文章的提示词"""
        return f"""
        你现在是一个科技资讯公众号编辑，需要根据以下几篇文章的信息整合生成一篇科技资讯公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于最新科技动态的公众号文章，要求：
        1. 注重科技新闻的时效性和准确性
        2. 结构清晰，分段合理，可以按不同科技领域（如硬件、软件、AI等）分类
        3. 用通俗易懂的语言解释复杂的科技概念
        4. 关注行业趋势，提供有见地的分析
        5. 文末可以添加对科技发展的展望
        6. 保留原文中的重要链接
        
        生成高质量的科技资讯文章。
        """
