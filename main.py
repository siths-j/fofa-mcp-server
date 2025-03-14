# -*- coding: utf-8 -*-
import base64
import os
from typing import Any, Coroutine, Dict
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
            if data.get("error"):
                data["results"] = [
                    dict(zip(FOFA_FIELDS.split(","), item))
                    for item in data["results"]
                ]
            return data
        return None
    except httpx.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    return None


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
    formatted["summary"] = "\n".join(summary)
    if data.get('error'):
        return {"summary": "\n".join(summary) + f"\n错误提示: {data.get('errmsg', '未知错误')}", "data": []}

    if not data.get('results'):
        return {"summary": "\n".join(summary) + "\n未找到匹配结果", "data": []}

    result = data.get('results')

    for item in result:
        if fields == 'all':
            info = {
                "IP": item[0],
                "端口": item[1],
                "协议": item[2],
                "国家代码": item[3],
                "国家名": item[4],
                "地区": item[5],
                "城市": item[6],
                "经度": item[7],
                "纬度": item[8],
                "ASN编号": item[9],
                "ASN组织": item[10],
                "主机名": item[11],
                "域名": item[12],
                "操作系统": item[13],
                "服务器": item[14],
                "ICP备案号": item[15],
                "网站标题": item[16],
                "JARM指纹": item[17],
                "Header": item[18],
                "Banner": item[19],
                "基础协议": item[20],
                "URL链接": item[21],
                "证书颁发者组织": item[22],
                "证书颁发者通用名称": item[23],
                "证书持有者组织": item[24],
                "证书持有者通用名称": item[25],
                "JA3S指纹": item[26],
                "TLS版本": item[27],
                "产品名": item[28],
                "产品分类": item[29],
                "版本号": item[30],
                "最后更新时间": item[31],
                "域名CNAME": item[32]
            }
        else:
            info = {
                "IP": item[0],
                "端口": item[1],
                "协议": item[2],
                "主机名": item[3],
                "域名": item[4],
                "ICP备案号": item[5],
                "网站标题": item[6],
                "产品名": item[7],
                "版本号": item[8],
                "最后更新时间": item[9]
            }
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
async def fofa_search_tool(query: str, fields="", size: int = 50) -> dict[str, Any] | None:
    """ 使用 FOFA API 进行查询，返回更多字段信息 """
    result = await fofa_search(query, fields, size, )
    return format_info(result, fields) if result else None


@mcp.tool()
async def fofa_userinfo_tool() -> Coroutine[Any, Any, Any | None]:
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
