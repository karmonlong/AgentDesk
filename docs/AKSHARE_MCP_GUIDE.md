# AKShare MCP 工具使用指南

## 概述

本项目集成了 `@aahl/mcp-aktools` MCP 服务器，提供 18 个财经数据工具。

## 配置

配置位于 `mcp_servers.json`:

```json
{
  "mcpServers": {
    "mcp-aktools": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@aahl/mcp-aktools",
        "--key",
        "44c67169-65b8-4564-8c17-90bc6746c6e7"
      ]
    }
  }
}
```

## 可用工具列表

### ✅ 已验证可用的工具

1. **get_current_time** - 获取当前时间和交易日信息
   - 参数: 无
   - 示例: `{"tool": "get_current_time", "args": {}}`

2. **stock_info** - 获取股票基本信息
   - 参数: `symbol` (股票代码), `market` (市场，使用 "A" 表示A股)
   - 示例: `{"tool": "stock_info", "args": {"symbol": "000001", "market": "A"}}`

3. **stock_news** - 获取股票相关新闻
   - 参数: `symbol` (股票代码), `limit` (返回数量)
   - 示例: `{"tool": "stock_news", "args": {"symbol": "000001", "limit": 3}}`

### ⚠️ 部分可用的工具

4. **stock_prices** - 获取股票历史价格
   - 参数: `symbol`, `market`, `period` (如 "1d"), `limit`
   - 注意: 某些股票代码可能返回 "Not Found"，可能是数据源问题
   - 示例: `{"tool": "stock_prices", "args": {"symbol": "000001", "market": "A", "period": "1d", "limit": 10}}`

5. **search** - 搜索股票代码
   - 参数: `keyword` (关键词), `market` (市场)
   - 注意: 搜索功能可能对某些关键词返回 "Not Found"
   - 示例: `{"tool": "search", "args": {"keyword": "平安银行", "market": "A"}}`

### 📋 其他工具

6. **stock_indicators_a** - A股财务指标
7. **stock_indicators_hk** - 港股财务指标
8. **stock_indicators_us** - 美股财务指标
9. **stock_zt_pool_em** - 涨停股票池
10. **stock_zt_pool_strong_em** - 强势股池
11. **stock_lhb_ggtj_sina** - 龙虎榜数据
12. **stock_sector_fund_flow_rank** - 行业资金流向
13. **stock_news_global** - 全球财经快讯
14. **okx_prices** - OKX 加密货币价格
15. **okx_loan_ratios** - OKX 借贷比率
16. **okx_taker_volume** - OKX 主动买卖量
17. **binance_ai_report** - 币安 AI 分析报告
18. **trading_suggest** - 交易建议

## 参数格式规范

### 股票代码格式

**重要**: 使用纯数字代码，不要添加交易所后缀

- ✅ 正确: `"000001"` (平安银行)
- ✅ 正确: `"600036"` (招商银行)
- ❌ 错误: `"000001.SZ"`
- ❌ 错误: `"600036.SH"`

### 市场参数

- A股市场: `"market": "A"`
- 港股市场: `"market": "HK"` (如适用)
- 美股市场: `"market": "US"` (如适用)

### 时间周期参数

- `"period": "1d"` - 日线
- `"period": "1w"` - 周线
- `"period": "1m"` - 月线

## 使用示例

### 在 NewsAggregatorAgent 中使用

NewsAggregatorAgent 会自动识别工具调用请求，格式如下：

```json
{"tool": "stock_info", "args": {"symbol": "000001", "market": "A"}}
```

### 直接调用 MCP 工具

```python
from services.mcp_service import mcp_manager
from tools.akshare_helper import format_tool_args

# 格式化参数
tool_args = format_tool_args("stock_info", {
    "symbol": "000001",
    "market": "A"
})

# 调用工具
result = await mcp_manager.call_tool(
    "npx",
    ["-y", "@smithery/cli@latest", "run", "@aahl/mcp-aktools", "--key", "..."],
    "stock_info",
    tool_args
)
```

## 常见问题

### Q: 为什么 stock_prices 返回 "Not Found"？

A: 可能的原因：
1. 股票代码不存在或已退市
2. 数据源暂时不可用
3. 参数格式不正确（确保使用纯数字代码，market="A"）

### Q: 搜索功能不工作？

A: search 工具可能对某些关键词不返回结果。建议：
1. 使用完整的公司名称
2. 直接使用股票代码查询其他工具
3. 尝试不同的关键词

### Q: 如何获取更多数据？

A: 可以尝试：
1. 使用 `stock_indicators_a` 获取财务指标
2. 使用 `stock_news` 获取相关新闻
3. 使用 `get_current_time` 获取交易日信息

## 测试

运行测试脚本验证工具是否正常工作：

```bash
# 基础测试
python test_mcp_aktools.py

# 详细测试
python test_mcp_aktools_detailed.py
```

## 辅助函数

项目提供了 `tools/akshare_helper.py` 模块，包含：

- `normalize_stock_symbol()` - 规范化股票代码格式
- `format_tool_args()` - 格式化工具参数
- `validate_tool_args()` - 验证工具参数

这些函数会自动在 NewsAggregatorAgent 中使用，确保参数格式正确。














