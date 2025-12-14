"""
AKShare MCP 工具参数格式化辅助函数
用于规范化股票代码、市场参数等
"""
import re
from typing import Dict, Any, Optional


def normalize_stock_symbol(symbol: str, market: Optional[str] = None) -> Dict[str, str]:
    """
    规范化股票代码格式
    
    Args:
        symbol: 股票代码，可能是 "000001", "000001.SZ", "600000.SH" 等格式
        market: 市场代码，如 "A", "SH", "SZ" 等
    
    Returns:
        规范化后的参数字典，包含 symbol 和 market
    """
    if not symbol:
        return {"symbol": "", "market": market or "A"}
    
    symbol = str(symbol).strip()
    
    # 如果已经包含交易所后缀 (如 000001.SZ, 600000.SH)
    if '.' in symbol:
        parts = symbol.split('.')
        code = parts[0]
        exchange = parts[1].upper()
        
        # 映射交易所代码
        if exchange in ['SZ', 'SZSE']:
            return {"symbol": code, "market": "A"}  # 深交所属于A股
        elif exchange in ['SH', 'SSE']:
            return {"symbol": code, "market": "A"}  # 上交所属于A股
        else:
            return {"symbol": code, "market": market or "A"}
    
    # 根据股票代码前缀判断市场
    if symbol.startswith('0') or symbol.startswith('3'):
        # 深交所股票 (000xxx, 002xxx, 300xxx)
        return {"symbol": symbol, "market": "A"}
    elif symbol.startswith('6'):
        # 上交所股票 (600xxx, 601xxx, 603xxx, 688xxx)
        return {"symbol": symbol, "market": "A"}
    elif symbol.startswith('8') or symbol.startswith('4'):
        # 北交所或新三板
        return {"symbol": symbol, "market": "A"}
    else:
        # 默认使用提供的 market 或 "A"
        return {"symbol": symbol, "market": market or "A"}


def format_tool_args(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据工具名称格式化参数
    
    Args:
        tool_name: 工具名称
        tool_args: 原始参数
    
    Returns:
        格式化后的参数
    """
    formatted_args = tool_args.copy()
    
    # 需要股票代码的工具
    stock_tools = [
        'stock_info', 'stock_prices', 'stock_news', 
        'stock_indicators_a', 'stock_indicators_hk', 'stock_indicators_us'
    ]
    
    if tool_name in stock_tools:
        if 'symbol' in formatted_args:
            symbol = formatted_args.get('symbol', '')
            market = formatted_args.get('market')
            normalized = normalize_stock_symbol(symbol, market)
            formatted_args.update(normalized)
    
    # stock_prices 需要 period 和 limit
    if tool_name == 'stock_prices':
        if 'period' not in formatted_args:
            formatted_args['period'] = '1d'
        if 'limit' not in formatted_args:
            formatted_args['limit'] = 10
    
    # stock_news 需要 limit
    if tool_name == 'stock_news':
        if 'limit' not in formatted_args:
            formatted_args['limit'] = 5
    
    # search 工具使用不同的 market 格式：sh, sz, hk, us
    if tool_name == 'search':
        if 'market' not in formatted_args:
            formatted_args['market'] = 'sh'  # 默认使用上证
        else:
            # 如果用户提供了 'A'，需要转换为 'sh' 或 'sz'
            # 但这里我们保持原值，因为 search 工具期望 sh/sz/hk/us
            market = formatted_args.get('market', '').lower()
            if market == 'a':
                # A股默认使用上证
                formatted_args['market'] = 'sh'
    
    return formatted_args


def validate_tool_args(tool_name: str, tool_args: Dict[str, Any]) -> tuple:
    """
    验证工具参数是否有效
    
    Returns:
        (is_valid, error_message)
    """
    # stock_info, stock_prices 需要 symbol 和 market
    if tool_name in ['stock_info', 'stock_prices']:
        if 'symbol' not in tool_args or not tool_args['symbol']:
            return False, f"{tool_name} 需要 symbol 参数"
        if 'market' not in tool_args:
            return False, f"{tool_name} 需要 market 参数"
    
    # stock_news 需要 symbol
    if tool_name == 'stock_news':
        if 'symbol' not in tool_args or not tool_args['symbol']:
            return False, "stock_news 需要 symbol 参数"
    
    # search 需要 keyword
    if tool_name == 'search':
        if 'keyword' not in tool_args or not tool_args['keyword']:
            return False, "search 需要 keyword 参数"
    
    return True, None

