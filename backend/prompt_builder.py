import json

def build_report_prompt(prompt, summary, chart_data, filters,report_type, report_length, modules):
    length_instruction_map = {
        "short": "请输出精简版分析专报，控制在300-500字，分段简洁。",
        "standard": "请输出标准版分析专报，控制在600-900字。",
        "long": "请输出较详细的分析专报，控制在1000-1500字。",
        "bullet": "请采用分点汇报版输出，每部分3-5条，语言简洁有力。"
    }

    report_type_map = {
        "management": "面向高校管理层，强调整体趋势、问题识别与决策建议。",
        "enrollment": "面向招生工作，强调生源匹配、专业吸引力与招生优化建议。",
        "training": "面向培养优化，强调课程设置、能力结构与岗位匹配。",
        "employment": "面向就业指导，强调就业去向、岗位推荐与能力提升建议。"
    }

    length_instruction = length_instruction_map.get(
        report_length,
        "请输出标准版分析专报，控制在600-900字。"
    )

    type_instruction = report_type_map.get(
        report_type,
        "面向高校管理层，强调整体趋势、问题识别与决策建议。"
    )
    region = filters.get('region', '上海')
    version = filters.get('version', '当前版本')
    current_page = filters.get('currentPage', 'report')

    return f"""
你是一名高校就业分析与管理决策顾问。

请基于以下平台数据，生成一份面向高校管理者的分析专报。

【用户要求】
{prompt}

【报告类型】
{report_type}
{type_instruction}

【报告篇幅】
{report_length}
{length_instruction}

【纳入模块】
{json.dumps(modules, ensure_ascii=False)}

【区域信息】
{filters.get('region', '上海')}

【数据版本】
{version}

【平台摘要】
{json.dumps(summary, ensure_ascii=False, indent=2)}

【图表摘要】
{json.dumps(chart_data, ensure_ascii=False, indent=2)}

写作要求：
1. 使用正式、专业、简洁的中文。
2. 输出结构包括：总体情况、主要发现、问题分析、对策建议、结论。
3. 结论必须结合具体数据，不要空泛。
4. 优先使用平台已提供的数据，不要编造不存在的字段。
5. 如果某些数据不足以支持强结论，要明确说明“基于当前样本可初步判断”。
6. 避免长句堆砌，尽量提高可读性。输出适合直接放入高校管理汇报材料中。
"""