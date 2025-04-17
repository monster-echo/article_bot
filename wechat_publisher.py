import html
import os
import json
import requests
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import time
import mimetypes
import hashlib
import base64
from urllib.parse import urlparse

from config import AISTUDIOX_API_URL

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 从环境变量获取微信公众号配置
APPID = os.getenv("WEIXIN_APPID")
APPSECRET = os.getenv("WEIXIN_APPSECRET")

# 微信API接口
ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
PUBLISH_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/submit"
UPLOAD_IMG_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"  # 上传图片到微信服务器的永久素材接口
UPLOAD_material_URL = (
    "https://api.weixin.qq.com/cgi-bin/material/add_material"  # 上传永久
)


# 缓存access_token
token_cache = {"access_token": None, "expires_at": None}


def get_access_token():
    """
    获取微信公众号访问令牌
    """
    # 检查缓存的token是否有效
    now = datetime.now()
    if (
        token_cache["access_token"]
        and token_cache["expires_at"]
        and now < token_cache["expires_at"]
    ):
        logger.info("使用缓存的access_token")
        return token_cache["access_token"]

    # 获取新的access_token
    params = {"grant_type": "client_credential", "appid": APPID, "secret": APPSECRET}

    try:
        logger.info("正在获取新的access_token...")
        response = requests.get(ACCESS_TOKEN_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "access_token" in data:
            # 缓存token，设置过期时间比实际提前5分钟
            token_cache["access_token"] = data["access_token"]
            token_cache["expires_at"] = now + timedelta(
                seconds=data["expires_in"] - 300
            )
            logger.info(f"获取access_token成功，有效期至: {token_cache['expires_at']}")
            return data["access_token"]
        else:
            logger.error(f"获取access_token失败: {data}")
            raise Exception(f"获取access_token失败: {data.get('errmsg', '未知错误')}")
    except Exception as e:
        logger.error(f"获取access_token时发生错误: {str(e)}")
        raise


def create_draft(
    title, content, thumb_media_id=None, author="", digest="", content_source_url=""
):
    """
    创建草稿

    参数:
        title: 文章标题
        content: 文章内容，支持HTML
        thumb_media_id: 封面图片media_id
        author: 作者
        digest: 摘要
        content_source_url: 原文链接
        need_open_comment: 开打评论 0不打开 1打开

    返回:
        草稿media_id
    """
    access_token = get_access_token()

    # 准备文章数据
    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content,
        "content_source_url": content_source_url,
        "need_open_comment": 1,
    }

    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id

    data = {"articles": [article]}

    try:
        logger.info(f"正在创建草稿: {title}")
        # 这里需要转成data，直接用json会出现乱码
        json_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        response = requests.post(
            f"{DRAFT_ADD_URL}?access_token={access_token}",
            data=json_data,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        response.raise_for_status()
        result = response.json()

        if "media_id" in result:
            logger.info(f"草稿创建成功，media_id: {result.get('media_id')}")
            return result.get("media_id")
        else:
            logger.error(f"创建草稿失败: {result}")
            raise Exception(f"创建草稿失败: {result.get('errmsg', '未知错误')}")
    except Exception as e:
        logger.error(f"创建草稿时发生错误: {str(e)}")
        raise


def publish_draft(media_id):
    """
    发布草稿

    参数:
        media_id: 草稿的media_id

    返回:
        发布任务的publish_id
    """
    access_token = get_access_token()

    data = {"media_id": media_id}

    try:
        logger.info(f"正在发布草稿，media_id: {media_id}")
        response = requests.post(
            f"{PUBLISH_URL}?access_token={access_token}", json=data
        )
        response.raise_for_status()
        result = response.json()

        if result.get("errcode") == 0:
            logger.info(f"发布成功，publish_id: {result.get('publish_id')}")
            return result.get("publish_id")
        else:
            logger.error(f"发布失败: {result}")
            raise Exception(f"发布失败: {result.get('errmsg', '未知错误')}")
    except Exception as e:
        logger.error(f"发布草稿时发生错误: {str(e)}")
        raise


def download_image(image_url):
    """
    下载图片

    参数:
        image_url: 图片URL

    返回:
        (image_content, filename, mime_type)
    """
    try:
        logger.info(f"正在下载图片: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # 如果URL没有文件名，生成一个随机名称
        hash_object = hashlib.md5(image_url.encode())
        filename = f"{hash_object.hexdigest()}.jpg"

        # 获取MIME类型
        content_type = response.headers.get("Content-Type")
        if not content_type or content_type == "application/octet-stream":
            # 尝试从文件名判断MIME类型
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "image/jpeg"  # 默认为JPEG
        else:
            mime_type = content_type

        return response.content, filename, mime_type
    except Exception as e:
        logger.error(f"下载图片失败: {str(e)}")
        raise


def upload_image(image_url_or_path):
    """
    上传图片到微信服务器，用于公众号文章内部图片

    参数:
        image_url_or_path: 图片URL或本地路径

    返回:
        图片URL
    """
    access_token = get_access_token()

    try:
        # 判断是URL还是本地路径
        if image_url_or_path.startswith(("http://", "https://")):
            image_content, filename, mime_type = download_image(image_url_or_path)
        else:
            # 读取本地文件
            with open(image_url_or_path, "rb") as f:
                image_content = f.read()
            filename = os.path.basename(image_url_or_path)
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "image/jpeg"

        # 上传图片
        logger.info(f"正在上传图片到微信服务器: {filename}")
        files = {"media": (filename, image_content, mime_type)}

        response = requests.post(
            f"{UPLOAD_IMG_URL}?access_token={access_token}", files=files
        )
        response.raise_for_status()
        result = response.json()

        if "url" in result:
            logger.info(f"图片上传成功: {result['url']}")
            return result["url"]
        else:
            logger.error(f"上传图片失败: {result}")
            raise Exception(f"上传图片失败: {result.get('errmsg', '未知错误')}")
    except Exception as e:
        logger.error(f"上传图片过程中发生错误: {str(e)}")
        raise


def upload_material(image_url_or_path):
    """
    上传素材

    参数:
        image_url_or_path: 图片URL或本地路径

    返回:
        media_id
    """
    access_token = get_access_token()

    try:
        # 判断是URL还是本地路径
        if image_url_or_path.startswith(("http://", "https://")):
            image_content, filename, mime_type = download_image(image_url_or_path)
        else:
            # 读取本地文件
            with open(image_url_or_path, "rb") as f:
                image_content = f.read()
            filename = os.path.basename(image_url_or_path)
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "image/jpeg"

        # 上传图片
        logger.info(f"正在上传封面图片: {filename}")
        files = {"media": (filename, image_content, mime_type)}

        response = requests.post(
            f"{UPLOAD_material_URL}?access_token={access_token}&type=image", files=files
        )
        response.raise_for_status()
        result = response.json()

        if "media_id" in result:
            logger.info(f"封面图片上传成功, media_id: {result['media_id']}")
            return result["media_id"]
        else:
            logger.error(f"上传封面图片失败: {result}")
            raise Exception(f"上传封面图片失败: {result.get('errmsg', '未知错误')}")
    except Exception as e:
        logger.error(f"上传封面图片过程中发生错误: {str(e)}")
        raise


def process_article_content(content, image_urls=None):
    """
    处理文章内容，上传图片到微信服务器

    参数:
        content: 原始文章内容
        image_urls: 需要处理的图片URL列表，如果为None则自动从content中提取

    返回:
        处理后的文章内容
    """
    import re

    # 如果没有提供图片列表，从内容中提取
    if image_urls is None:
        image_urls = re.findall(r'<img[^>]+src="([^"]+)"', content)

    # 替换图片URL
    for old_url in image_urls:
        try:
            download_url = html.unescape(old_url)
            # 跳过已经是微信域名的图片
            if "mmbiz.qpic.cn" in download_url:
                logger.info(f"跳过已经是微信域名的图片: {download_url}")
                continue

            if download_url.startswith("/api/oss"):
                # 处理OSS图片
                download_url = f"{AISTUDIOX_API_URL}{old_url}"

            # 上传图片到微信服务器
            new_url = upload_image(download_url)

            # 替换URL
            content = content.replace(old_url, new_url)
            logger.info(f"图片URL已替换: {old_url} -> {new_url}")
        except Exception as e:
            logger.warning(f"处理图片 {old_url} 失败，保留原URL: {str(e)}")
            raise

    return content


def publish_article(
    title,
    content,
    author="",
    digest="",
    content_source_url="",
    thumb_media_id=None,
    thumb_url=None,
    process_images=True,
):
    """
    发布文章到微信公众号

    参数:
        title: 文章标题
        content: 文章内容，支持HTML
        author: 作者
        digest: 摘要
        content_source_url: 原文链接
        thumb_media_id: 封面图片media_id，优先使用
        thumb_url: 封面图片URL，当thumb_media_id为None时使用
        process_images: 是否处理文章中的图片

    返回:
        是否发布成功
    """
    try:
        # 处理封面图片
        if not thumb_media_id and thumb_url:
            try:
                thumb_media_id = upload_material(thumb_url)
            except Exception as e:
                raise Exception(f"上传封面图片失败，将使用默认封面: {str(e)}")

        # 处理文章内容中的图片
        if process_images:
            content = process_article_content(content)

        # 创建草稿
        media_id = create_draft(
            title=title,
            content=content,
            author=author,
            digest=digest,
            content_source_url=content_source_url,
            thumb_media_id=thumb_media_id,
        )

        # # 发布草稿
        # publish_id = publish_draft(media_id)

        return {"success": True, "media_id": media_id, "publish_id": None}
    except Exception as e:
        logger.error(f"发布文章失败: {str(e)}")
        return {"success": False, "error": str(e)}


def main():
    """测试函数"""
    # title = "测试文章标题"
    # content = """
    # <h1>这是一篇测试文章</h1>
    # <p>这是文章内容，支持HTML格式。</p>
    # <p>您可以在这里添加<strong>格式化</strong>的内容。</p>
    # """
    # author = "Echo072"
    # digest = "这是一篇测试文章的摘要"
    # thumb_url = "https://www.aistudiox.design/api/oss?ossKey=db9c7bc7/photo_2025-04-07_14-00-02.jpg"  # 测试封面图

    # result = publish_article(
    #     title=title, content=content, author=author, digest=digest, thumb_url=thumb_url
    # )
    # print(result)

    access_token = get_access_token()


if __name__ == "__main__":
    main()
