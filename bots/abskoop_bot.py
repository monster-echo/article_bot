from bots.base import BotBase


class AbskoopBot(BotBase):
    interval = 60 * 60  # 每小时执行一次
    file_prefix = "abskoop-Telegram-"
    output_folder = "resources"
    output_prefix = "resources"

    def generate_title_prompt(self, article_content):
        """生成资源分享标题的提示词"""
        return f"""
        你现在是一个资源分享公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个吸引人的、能够引起用户兴趣的资源分享公众号文章标题。标题应当简洁明了，突出内容的实用价值。
        """

    def generate_article_prompt(self, articles_info):
        """生成资源分享文章的提示词"""
        return f"""
        你现在是一个资源分享公众号编辑，需要根据以下几篇文章的信息整合生成一篇资源分享公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于实用资源、工具和软件的公众号文章，要求：
        1. 按资源类型进行分类（如软件工具、学习资源、AI工具等）
        2. 每个资源介绍要简洁明了，突出其核心价值和使用场景
        3. 对于重要或热门的资源进行重点介绍
        4. 保留原资源的链接，确保读者可以直接访问
        5. 适当添加一些使用建议或个人评价
        6. 文末可以总结本次分享的资源特点或价值
        
        生成高质量的实用资源分享文章。
        """
