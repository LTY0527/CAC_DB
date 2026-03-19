from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'success': True,
        'message': 'backend is running'
    })

@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    data = request.get_json()

    prompt = data.get('prompt', '')
    current_page = data.get('currentPage', '')
    chart_data = data.get('chartData', {})
    filters = data.get('filters', {})

    # 1. 取前端传来的数据，没有就用默认值
    employment_rate = chart_data.get('employmentRate', [88, 89, 91, 90, 92])
    stay_shanghai_rate = chart_data.get('stayShanghaiRate', [52, 55, 57, 58, 60])
    salary_data = chart_data.get('salaryData', [14500, 13200, 11800, 10900, 9800, 10100])

    # 2. 做简单计算
    avg_employment = round(sum(employment_rate) / len(employment_rate), 1)
    avg_stay_shanghai = round(sum(stay_shanghai_rate) / len(stay_shanghai_rate), 1)
    max_salary = max(salary_data)
    min_salary = min(salary_data)
    salary_gap = max_salary - min_salary

    # 3. 生成更像真实分析的报告
    report = f"""
一、总体情况
当前页面为：{current_page}。
结合现有图表与筛选条件，高校就业总体态势较为稳定。
从总体指标看，样本高校平均就业率约为 {avg_employment}%，平均留沪率约为 {avg_stay_shanghai}%。整体表现说明高校毕业生就业基本盘较稳，但留沪转化仍有进一步提升空间。
二、主要发现
1. 就业趋势较为平稳
近五期就业率数据为：{employment_rate}。整体波动不大，并呈现缓慢上升趋势，说明当前就业工作整体具有一定稳定性。
2. 留沪比例稳中有升
近五期留沪率数据为：{stay_shanghai_rate}。相较前期，留沪水平呈上升态势，但与重点产业对本地人才吸纳需求相比，仍存在提升空间。
3. 薪资差异较为明显
专业薪资数据为：{salary_data}。其中最高月薪约为 {max_salary} 元，最低约为 {min_salary} 元，专业间薪资差距约为 {salary_gap} 元，说明不同专业在就业质量上存在明显分层。
4. 当前筛选条件
本次分析所依据的筛选条件为：{filters}。
当前分析需求为：{prompt}
三、问题分析  
1. 高校专业结构与本地重点产业之间仍存在结构性错位  
2. 留沪意愿与岗位吸引力之间存在一定落差  
3. 就业质量（薪资、发展空间）存在明显分层  
四、对策建议  
1. 优化专业布局  
重点加强与人工智能、集成电路、金融科技等产业相关专业建设  
2. 提升本地岗位吸引力  
通过政策引导，提高重点行业起薪水平与职业发展通道  
3. 强化就业服务能力  
建立高校—企业—政府三方协同机制，提升岗位匹配效率  
4. 建立数据监测机制  
持续跟踪就业率、留沪率与薪资变化，形成动态分析专报体系
"""

    return jsonify({
        'success': True,
        'report': report
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)