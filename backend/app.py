# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import json
# import os

# app = Flask(__name__)
# CORS(app)

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR = os.path.join(BASE_DIR, 'data')

# def load_json(filename):
#     file_path = os.path.join(DATA_DIR, filename)
#     with open(file_path, 'r', encoding='utf-8') as f:
#         return json.load(f)

# @app.route('/api/health', methods=['GET'])
# def health():
#     return jsonify({
#         'success': True,
#         'message': 'backend is running'
#     })

# @app.route('/api/employment-summary', methods=['GET'])
# def get_employment_summary():
#     data = load_json('employment_summary.json')
#     return jsonify({'success': True, 'data': data})


# @app.route('/api/salary-forecast', methods=['GET'])
# def get_salary_forecast():
#     data = load_json('salary_forecast.json')
#     return jsonify({'success': True, 'data': data})


# @app.route('/api/enrollment-matching', methods=['GET'])
# def get_enrollment_matching():
#     data = load_json('enrollment_matching.json')
#     return jsonify({'success': True, 'data': data})


# @app.route('/api/major-matching-rules', methods=['GET'])
# def get_major_matching_rules():
#     data = load_json('major_matching_rules.json')
#     return jsonify({'success': True, 'data': data})


# @app.route('/api/job-recommendation', methods=['GET'])
# def get_job_recommendation():
#     data = load_json('job_recommendation.json')
#     return jsonify({'success': True, 'data': data})

# @app.route('/api/report/generate', methods=['POST'])
# def generate_report():
#     data = request.get_json()

#     prompt = data.get('prompt', '')
#     current_page = data.get('currentPage', '')
#     chart_data = data.get('chartData', {})
#     filters = data.get('filters', {})
#     summary = data.get('summary', {})

#     # 1. 取前端传来的数据，没有就用默认值
#     employment_rate = chart_data.get('employmentRate', [88, 89, 91, 90, 92])
#     stay_shanghai_rate = chart_data.get('stayShanghaiRate', [52, 55, 57, 58, 60])
#     salary_data = chart_data.get('salaryData', [14500, 13200, 11800, 10900, 9800, 10100])

#     # 2. 做简单计算
#     avg_employment = round(sum(employment_rate) / len(employment_rate), 1)
#     avg_stay_shanghai = round(sum(stay_shanghai_rate) / len(stay_shanghai_rate), 1)
#     max_salary = max(salary_data) if salary_data else 0
#     min_salary = min(salary_data) if salary_data else 0
#     salary_gap = max_salary - min_salary

#     salary_gap_text = f"{salary_gap:.2f}"
#     avg_employment_text = f"{avg_employment:.1f}"
#     avg_stay_text = f"{avg_stay_shanghai:.1f}"

#     region_text = filters.get('region', '上海')
#     version_text = filters.get('version', '当前版本')

#     # 3. 生成更像真实分析的报告
#     report = f"""一、总体情况
# 当前分析基于 {region_text} 地区相关就业数据，结合平台现有监测结果，
# 高校毕业生就业整体运行较为平稳。样本高校平均就业率约为 {avg_employment_text}% ，
# 平均留沪率约为 {avg_stay_text}% ，说明当前就业基本盘总体稳定，但在留沪转化和岗位吸引力方面仍有进一步提升空间。
# 二、主要发现
# 1. 就业形势总体平稳
# 近期就业表现保持在相对稳定区间，整体波动幅度不大，说明高校毕业生就业工作具备一定连续性和稳定性。
# 2. 留沪转化水平持续改善
# 从当前监测结果看，留沪比例呈现稳中有升态势，但与重点产业对本地人才的吸纳需求相比，仍有进一步提升空间。
# 3. 专业之间就业质量存在一定分层
# 不同专业在起薪水平、岗位质量和产业匹配方向上表现出一定差异，当前样本中专业薪资差距约为 {salary_gap_text} 元，
# 说明专业结构与岗位需求之间仍存在结构性差异。
# 4. 招生、培养与就业之间需要进一步协同
# 结合平台多模块结果，可以看出专业设置、培养路径和岗位去向之间仍需加强联动分析，
# 以提升高校人才培养与区域产业需求之间的匹配度。
# 三、问题分析
# 1. 部分专业结构与重点产业需求之间仍存在错位现象。
# 2. 留沪意愿与岗位吸引力之间仍存在一定落差。
# 3. 就业质量在不同专业之间表现不够均衡。
# 4. 招生端、培养端与就业端的数据联动分析仍有优化空间。
# 四、对策建议
# 1. 优化专业布局
# 围绕人工智能、集成电路、金融科技等重点产业方向，动态优化专业结构与人才培养重点。
# 2. 提升本地岗位吸引力
# 通过校地合作、企业协同和就业服务机制优化，增强优质岗位对毕业生的吸引作用。
# 3. 强化招生与就业联动
# 将招生匹配结果与后续培养过程、就业结果结合起来，形成更完整的全过程分析链条。
# 4. 建立动态监测机制
# 持续跟踪就业率、留沪率、薪资变化与岗位分布情况，逐步形成常态化、可追踪的分析专报体系。
# 五、结论
# 总体来看，当前版本（{version_text}）所支撑的数据分析结果表明，
# 高校毕业生就业工作整体保持稳定运行，但在专业结构优化、重点产业对接、
# 本地人才留用和全过程协同分析方面仍存在提升空间。后续可继续依托平台的数据更新与智能分析能力，
# 逐步增强面向高校管理场景的辅助决策支撑能力。
# """

#     return jsonify({
#         'success': True,
#         'report': report
#     })

# if __name__ == '__main__':
#     app.run(debug=True, host='127.0.0.1', port=5000)

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

from prompt_builder import build_report_prompt
from llm_client import call_llm

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json(filename):
    file_path = os.path.join(DATA_DIR, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'success': True,
        'message': 'backend is running'
    })

@app.route('/api/employment-summary', methods=['GET'])
def get_employment_summary():
    data = load_json('employment_summary.json')
    return jsonify({'success': True, 'data': data})

@app.route('/api/salary-forecast', methods=['GET'])
def get_salary_forecast():
    data = load_json('salary_forecast.json')
    return jsonify({'success': True, 'data': data})

@app.route('/api/enrollment-matching', methods=['GET'])
def get_enrollment_matching():
    data = load_json('enrollment_matching.json')
    return jsonify({'success': True, 'data': data})

@app.route('/api/major-matching-rules', methods=['GET'])
def get_major_matching_rules():
    data = load_json('major_matching_rules.json')
    return jsonify({'success': True, 'data': data})

@app.route('/api/job-recommendation', methods=['GET'])
def get_job_recommendation():
    data = load_json('job_recommendation.json')
    return jsonify({'success': True, 'data': data})

@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    try:
        data = request.get_json() or {}
        print("收到请求数据：", data)

        prompt = data.get('prompt', '')
        current_page = data.get('currentPage', 'report')
        report_type = data.get('reportType', 'management')
        report_length = data.get('reportLength', 'standard')
        modules = data.get('modules', [])
        chart_data = data.get('chartData', {})
        filters = data.get('filters', {})
        summary = data.get('summary', {})

        filters['currentPage'] = current_page

        prompt_text = build_report_prompt(
            prompt=prompt,
            summary=summary,
            chart_data=chart_data,
            filters=filters,
            report_type=report_type,
            report_length=report_length,
            modules=modules,
        )

        print("Prompt 构造成功，开始调用大模型...")
        report = call_llm(prompt_text)
        print("大模型调用成功")

        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    # except Exception as e:
    #     return jsonify({
    #         'success': False,
    #         'message': f'报告生成失败: {str(e)}'
    #     }), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)