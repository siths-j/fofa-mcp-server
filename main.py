# -*- coding: utf-8 -*-
import base64
import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# FOFA API 配置
FOFA_KEY = os.getenv("FOFA_KEY")
FOFA_API_URL = "https://fofa.info/api/v1"
# 需要查询的字段
FOFA_FIELDS_ALL = "ip,port,protocol,country,country_name,region,city,longitude,latitude,as_number,as_organization,host,domain,os,server,icp,title,jarm,header,banner,base_protocol,link,certs_issuer_org,certs_issuer_cn,certs_subject_org,certs_subject_cn,tls_ja3s,tls_version,product,product_category,version,lastupdatetime,cname"

FOFA_FIELDS = "ip,port,protocol,host,domain,icp,title,product,version,lastupdatetime"
# 初始化 MCP Server
mcp = FastMCP("FOFA-MCP-Server")
request_session = httpx.AsyncClient()


# FOFA API 查询封装


async def fofa_search(query: str, fields: str, size: int = 50) -> dict[str, Any] | None:
    """执行 FOFA 查询"""
    query_base64 = base64.b64encode(query.encode()).decode()
    if fields == 'all':
        fields = FOFA_FIELDS_ALL
    else:
        fields = FOFA_FIELDS
    params = {
        "key": FOFA_KEY,
        "qbase64": query_base64,
        "size": size,
        "fields": fields
    }
    headers = {"Accept-Encoding": "gzip"}
    URL = f"{FOFA_API_URL}/search/all"
    try:
        response = await request_session.get(URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(data)
        if data:
            return data
        return None
    except httpx.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    return None


async def fofa_stats(query: str, aggs: str) -> dict[str, Any] | None:
    """执行 FOFA 聚合查询"""
    query_base64 = base64.b64encode(query.encode()).decode()
    params = {
        "key": FOFA_KEY,
        "qbase64": query_base64,
        "aggs": aggs
    }
    headers = {"Accept-Encoding": "gzip"}
    URL = f"{FOFA_API_URL}/search/stats"
    try:
        response = await request_session.get(URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        return None
    except httpx.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def format_stats_info(data: dict[str, Any]) -> dict[str, Any]:
    """格式化聚合查询结果"""
    if not data or data.get("error"):
        return {"summary": f"聚合查询失败: {data.get('errmsg', '未知错误')}", "data": {}}

    summary_list = [
        f"查询语句: {data.get('query', '')}",
        f"结果总数: {data.get('total', 0)}",
        "---"
    ]
    # 使用 .get() 安全地访问 'aggregations'
    aggregations = data.get('aggs', {})
    if not aggregations:
        summary_list.append("没有返回聚合结果。")

    formatted_data = {}

    for agg_name, buckets in aggregations.items():
        summary_list.append(f"聚合字段: {agg_name}")
        agg_results = []
        for bucket in buckets:
            agg_results.append(f"  - {bucket['name']}: {bucket['count']}")
        formatted_data[agg_name] = "\n".join(agg_results)

    return {"summary": "\n".join(summary_list), "data": formatted_data}


def format_info(data: dict[str, Any], fields: str) -> dict[str, Any]:
    """格式化查询结果"""
    if not data:
        return {"summary": "未找到结果", "data": []}
    formatted = {}
    formatted["data"] = []
    # 添加查询统计信息
    summary = [
        f"查询状态: {'成功' if not data.get('error', True) else '失败'}",
        f"消耗点数: {data.get('consumed_fpoint', 0)}",
        f"所需点数: {data.get('required_fpoints', 0)}",
        f"结果总数: {data.get('size', 0)}",
        f"当前页数: {data.get('page', 1)}",
        f"查询模式: {data.get('mode', 'extended')}",
        f"查询语句: {data.get('query', '')}"
    ]

    if data.get('error'):
        summary.append(f"错误提示: {data.get('errmsg', '未知错误')}")
        formatted["summary"] = "\n".join(summary)
        return formatted

    formatted["summary"] = "\n".join(summary)
    if not data.get('results'):
        return {"summary": "\n".join(summary) + "\n未找到匹配结果", "data": []}

    results = data.get('results', [])

    # 根据 "fields" 参数确定要使用的字段列表
    field_list = []
    if fields == 'all':
        field_list = FOFA_FIELDS_ALL.split(',')
    else:
        # 默认使用 FOFA_FIELDS
        field_list = FOFA_FIELDS.split(',')

    for item in results:
        # 动态地将字段和结果配对
        info = dict(zip(field_list, item))
        formatted["data"].append(info)

    return formatted


async def fofa_userinfo() -> Any | None:
    """查询FOFA账户信息"""
    URL = f"{FOFA_API_URL}/info/my"
    params = {
        "key": FOFA_KEY
    }
    headers = {"Accept-Encoding": "gzip"}
    try:
        response = await request_session.get(URL, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


@mcp.tool()
async def fofa_search_tool(query: str, fields: str = "", size: int = 50) -> dict[str, Any]:
    """ 使用 FOFA API 进行查询，返回更多字段信息 """
    result = await fofa_search(query, fields, size)
    return format_info(result, fields) if result else {"summary": "查询失败", "data": []}


@mcp.tool()
async def fofa_stats_tool(query: str, aggs: str) -> dict[str, Any]:
    """
    使用 FOFA API 进行聚合查询。

    :param query: FOFA 查询语句。
    :param aggs: 聚合查询的字段，例如 "country,port"。
    :return: 聚合查询结果。
    """
    result = await fofa_stats(query, aggs)
    return format_stats_info(result) if result else {"summary": "聚合查询失败", "data": {}}


@mcp.tool()
async def fofa_userinfo_tool() -> dict[str, Any] | None:
    """ 查询 FOFA 账户信息 """
    return await fofa_userinfo()


if __name__ == "__main__":
    # import asyncio
    # # 测试异步函数调用

    # async def test_search():
    #     result = await fofa_search_tool("YXBwPSJuZ2lueCI=", 10)
    #     print(result)

    # # 运行测试函数
    # asyncio.run(test_search())
    # 启动MCP服务器
    mcp.run(transport='stdio')
