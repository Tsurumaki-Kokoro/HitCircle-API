import asyncio
from typing import Union, Dict, List

import httpx
from loguru import logger


async def httpx_request(method: str, url: str, headers: Dict[str, str] = None, data: Union[str, Dict[str, str]] = None,
                        params: Dict[str, str] = None, max_retries: int = 3, timeout: int = 5):
    """
    发送异步 HTTP 请求并处理超时重试，仅支持 JSON 格式的请求和响应

    :param method: 请求方法，如 'GET' 或 'POST'
    :param url: 请求的 URL
    :param headers: HTTP 请求头
    :param data: POST 请求的数据
    :param params: GET 请求的查询参数
    :param max_retries: 最大重试次数
    :param timeout: 请求超时时间（秒）
    :return: 响应的 JSON 对象，或在失败时抛出异常
    """
    retries = 0
    timeout_config = httpx.Timeout(timeout, connect=timeout)

    while retries < max_retries:
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.request(method, url, headers=headers, data=data, params=params)
                response.raise_for_status()
                return response.json()

        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            retries += 1
            logger.warning(f"Timeout occurred when requesting {url}, retrying... ({retries}/{max_retries})")

        except httpx.HTTPStatusError as e:
            # 处理非成功状态码
            logger.error(f"HTTP error occurred: {e.response.status_code} {e.response.text}")
            raise e

    logger.error("Maximum retry attempts reached, failing.")
    raise Exception("Maximum retry attempts reached, failing.")


async def httpx_download_request(url: str, max_retries: int = 3, timeout: int = 5):
    """
    发送异步 HTTP 请求并处理超时重试，仅支持下载文件

    :param url: 请求的 URL
    :param max_retries: 最大重试次数
    :param timeout: 请求超时时间（秒）
    :return: 响应的文件对象，或在失败时抛出异常
    """
    retries = 0
    timeout_config = httpx.Timeout(timeout, connect=timeout)

    while retries < max_retries:
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.request("GET", url)
                response.raise_for_status()
                return response

        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            retries += 1
            logger.warning(f"Timeout occurred when requesting {url}, retrying... ({retries}/{max_retries})")

        except httpx.HTTPStatusError as e:
            # 处理非成功状态码
            logger.error(f"HTTP error occurred: {e.response.status_code} {e.response.text}")
            raise e

    logger.error("Maximum retry attempts reached, failing.")
    raise Exception("Maximum retry attempts reached, failing.")


async def get_first_response(urls: List[str]):
    """
    并发请求多个 URL，返回第一个成功的响应

    :param urls: 请求的 URL 列表
    :return: 响应的 JSON 对象，或在所有请求失败时抛出异常
    """
    try:
        async with httpx.AsyncClient() as client:
            tasks = [client.get(url) for url in urls]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        raise Exception("Timeout occurred when requesting URLs.")

    except httpx.HTTPStatusError as e:
        # 处理非成功状态码
        logger.error(f"HTTP error occurred: {e.response.status_code} {e.response.text}")
        raise e

    for response in responses:
        if isinstance(response, httpx.Response):
            return response

    raise Exception("All requests failed.")
