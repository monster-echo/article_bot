import os
import re
import uuid
import requests
from pathlib import Path
from prompts import translate_prompt
from openai import OpenAI
import config


# 设置OpenAI API密钥
openai_client = OpenAI(api_key=config.MOONSHOT_API_KEY, base_url=config.OPENAI_BASE_URL)


def trim_thinking(text):
    """从文本中删除 <think> thinking </think>"""
    thinking_pattern = r"<think>.*?</think>"
    cleaned_text = re.sub(thinking_pattern, "", text, flags=re.DOTALL)
    return cleaned_text


def get_markdown_from_jina(url):
    """从Jina获取网页内容并转换为Markdown格式"""
    try:
        # 正确拼接Jina API URL
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"从Jina获取Markdown失败: {e}")
        return None


def translate(text):
    """使用 llm 翻译文章"""
    try:
        messages = [
            {
                "role": "system",
                "content": translate_prompt.format(text=text),
            }
        ]

        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )
        completion = openai_client.chat.completions.create(
            model="moonshot-v1-auto",
            messages=messages,
            temperature=0.3,
            max_tokens=8192,
        )

        assistant_message = completion.choices[0].message
        text = assistant_message.content
        return trim_thinking(text)
    except Exception as e:
        print(f"翻译失败: {e}")
        return text


def download_and_replace_images(folder, content):
    """下载文章中的所有图片并替换为本地路径"""

    article_folder = folder
    folder.mkdir(parents=True, exist_ok=True)

    def download_image(url):
        try:
            # 确保URL格式正确
            if not url.startswith(("http://", "https://")):
                return url

            # 提取文件名，如果没有合适的扩展名则使用默认名称
            filename = os.path.basename(url).split("?")[0]
            if not any(
                filename.lower().endswith(ext)
                for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
            ):
                filename = f"image_{hash(url)}.jpg"

            ext = Path(filename).suffix
            filename = f"{uuid.uuid4().hex}{ext}"
            local_path = folder / filename

            # 下载图片
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"已下载图片: {url} -> {local_path}")
            return f"images/{filename}"
        except Exception as e:
            print(f"下载图片失败 {url}: {e}")
            return url

    # 查找并替换Markdown中的图片链接
    def replace_image_url(match):
        alt_text = match.group(1) or "image"
        img_url = match.group(2)
        local_path = download_image(img_url)
        return f"![{alt_text}]({local_path})"

    # 使用正则表达式匹配Markdown中的图片
    pattern = r"!\[(.*?)\]\((.*?)\)"
    updated_content = re.sub(pattern, replace_image_url, content)
    return updated_content


def generate_article_id(url):
    """使用URL生成文章ID"""
    return uuid.uuid5(uuid.NAMESPACE_URL, url).hex[:6]


def main():
    """主函数"""
    # 获取输入的URL
    url = input("请输入要翻译的文章URL: ")
    id = generate_article_id(url)
    # 保存翻译后的文章
    article_folder = Path(f"articles/{id}")
    article_folder.mkdir(parents=True, exist_ok=True)

    print(f"正在从 {url} 获取内容...")
    markdown_content = get_markdown_from_jina(url)

    if not markdown_content:
        print("获取内容失败，请检查URL是否正确")
        return

    print("正在翻译文章内容...")
    translated_content = translate(markdown_content)

    print("正在下载并替换图片...")
    updated_content = download_and_replace_images(
        article_folder / "images", translated_content
    )

    original_file = Path(article_folder) / "original.md"
    with open(original_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    output_file = Path(article_folder) / f"index.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"翻译完成! 文件已保存至: {output_file}")


if __name__ == "__main__":
    main()
