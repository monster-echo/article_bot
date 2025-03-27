from bots.base import BotBase


class AiPostBot(BotBase):
    interval = 60 * 60  # 每小时执行一次
    min_files_required = 8  # 特定要求：至少需要8个文件
    file_prefix = "aipost-"
    output_folder = "aipost"
    output_prefix = "aipost"

    def generate_title_prompt(self, article_content):
        """生成公众号文章标题的提示词"""
        return f"""
        你现在是一个公众号文章专家，现在需要你根据几篇文章的标题和描述生成一篇公众号文章标题，要能增加点击量：
        
        文章集合: {article_content}
        
        请生成一篇公众号文章标题。
        """

    def generate_article_prompt(self, articles_info):
        """生成公众号文章的提示词"""
        return f"""
        你现在是一个公众号文章专家，现在需要你根据几篇文章的标题和描述生成一篇公众号文章，删除带有 aipost 的链接，删除广告内容，要能增加点击量：
        
        文章集合: {articles_info}
        
        请生成一篇内容丰富、结构清晰的公众号文章。
        """
