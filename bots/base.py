from abc import abstractmethod
import logging
import os
import json
from datetime import datetime
from bs4 import BeautifulSoup

from openai import OpenAI
import config
from langchain_ollama import OllamaLLM


# 设置OpenAI API密钥
openai_client = OpenAI(api_key=config.MOONSHOT_API_KEY, base_url=config.OPENAI_BASE_URL)
ollama_llm = OllamaLLM(model="deepseek-r1:32b")


class BotBase:
    interval = 60 * 60  # 默认每小时执行一次
    min_files_required = 5  # 默认最少需要5个文件
    file_prefix = ""  # 子类需要覆盖
    output_folder = "articles"  # 子类需要覆盖
    output_prefix = "article"  # 子类需要覆盖

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_files(self):
        """获取指定前缀的JSON文件"""
        folder = f"data/{datetime.now().strftime('%Y-%m-%d')}"
        files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.startswith(self.file_prefix) and f.endswith(".json")
        ]
        # 过滤掉带有"-created"后缀的文件
        return [f for f in files if not f.endswith("-created.json")]

    def clean_html(self, html_text):
        """移除HTML标签，保留纯文本内容"""
        if not html_text:
            return ""
        soup = BeautifulSoup(html_text, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    def extract_info_from_file(self, file_path):
        """从单个文件中提取信息，子类可以覆盖此方法来自定义提取逻辑"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article = json.load(f)

            # 提取基本信息
            title = article.get("title", "无标题")
            link = article.get("link", "")
            description = self.clean_html(article.get("description", ""))

            info = f"标题：{title}\n"
            info += f"链接：{link}\n"
            info += f"描述：{description}\n"

            return info
        except Exception as e:
            self.logger.error(f"提取文件信息时发生错误: {e}")
            return None

    def rename_processed_file(self, file_path):
        """重命名处理过的文件（添加-created后缀）"""
        try:
            file_dir, file_name = os.path.split(file_path)
            file_name_without_ext, file_ext = os.path.splitext(file_name)
            new_file_name = f"{file_name_without_ext}-created{file_ext}"
            new_file_path = os.path.join(file_dir, new_file_name)
            os.rename(file_path, new_file_path)
            return True
        except Exception as e:
            self.logger.error(f"重命名文件时发生错误: {e}")
            return False

    def create_output_dir(self):
        """创建输出目录"""
        output_dir = os.path.join("articles", self.output_folder)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_dir

    def generate_title(self, article_content):
        """根据文章内容生成标题"""
        try:
            prompt = self.generate_title_prompt(article_content[:2000])
            return self.llm(prompt)
        except Exception as e:
            self.logger.error(f"生成标题时发生错误: {e}")
            return f"{self.output_prefix}_{datetime.now().strftime('%Y-%m-%d')}"

    def generate_article(self, articles_info):
        """根据收集的信息生成文章"""
        try:
            prompt = self.generate_article_prompt(articles_info)
            return self.llm(prompt)
        except Exception as e:
            self.logger.error(f"生成文章时发生错误: {e}")
            return f"生成文章失败: {str(e)}"

    @abstractmethod
    def generate_title_prompt(self, article_content):
        """生成标题的提示词，子类必须实现"""
        pass

    @abstractmethod
    def generate_article_prompt(self, articles_info):
        """生成文章的提示词，子类必须实现"""
        pass

    def run(self):
        """执行机器人的主逻辑"""
        files = self.get_files()[:8]  # 只处理最新的8个文件

        if not files:
            self.logger.info(f"没有找到符合条件的{self.file_prefix}文件")
            return

        if len(files) < self.min_files_required:
            self.logger.info(
                f"{self.file_prefix}文件数量不足，至少需要{self.min_files_required}个文件"
            )
            return

        articles_info = ""

        # 从所有文件中收集信息
        for file in files:
            self.logger.info(f"开始处理{self.file_prefix}文件: {file}")
            info = self.extract_info_from_file(file)
            if info:
                articles_info += info + "\n\n"

        # 检查是否成功收集到信息
        if not articles_info:
            self.logger.info(f"没有成功提取到{self.file_prefix}文章信息")
            return

        self.logger.info(
            f"总共收集了 {len(files)} 篇{self.file_prefix}文章信息，开始生成公众号文章"
        )

        # 生成文章和标题
        try:
            article_content = self.generate_article(articles_info)
            title = self.generate_title(article_content)

            # 创建输出目录并保存文章
            output_dir = self.create_output_dir()
            output_file = os.path.join(
                output_dir,
                f"{self.output_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            )
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(article_content)
            self.logger.info(f"{self.file_prefix}文章已保存至: {output_file}")
        except Exception as e:
            self.logger.error(f"生成{self.file_prefix}文章时发生错误: {e}")
            return

        # 重命名处理过的文件
        for file in files:
            self.rename_processed_file(file)
        self.logger.info(
            f"已将处理过的{self.file_prefix}文件重命名（添加'-created'后缀）"
        )

    def llm(self, prompt):
        messages = [
            {
                "role": "system",
                "content": prompt,
            }
        ]
        completion = openai_client.chat.completions.create(
            model="moonshot-v1-auto",
            messages=messages,
            temperature=0.3,
            max_tokens=8192,
        )
        return completion.choices[0].message.content

        # # 使用Ollama LLM
        # return ollama_llm.invoke(prompt)
