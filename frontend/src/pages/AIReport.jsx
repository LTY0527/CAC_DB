// import { useState } from 'react'
// import { Card, Input, Button, Space } from 'antd'
// import axios from 'axios'

// const { TextArea } = Input

// const panelStyle = {
//   background: 'linear-gradient(180deg, rgba(7,26,47,0.96) 0%, rgba(4,18,34,0.96) 100%)',
//   border: '1px solid #1b4f7d',
//   borderRadius: 10,
//   boxShadow: '0 0 12px rgba(0, 153, 255, 0.12)',
// }

// const titleStyle = {
//   color: '#d9eeff',
//   fontSize: 16,
//   fontWeight: 600,
// }

// export default function AIReport() {
//   const [report, setReport] = useState('')
//   const [loading, setLoading] = useState(false)
//   const [promptText, setPromptText] = useState(
//     '请基于当前图表和筛选结果，生成面向高校管理者的就业分析专报。'
//   )

//   const handleGenerate = async () => {
//     try {
//       setLoading(true)

//       const res = await axios.post('http://127.0.0.1:5000/api/report/generate', {
//         prompt: promptText,
//         currentPage: 'report',
//         chartData: {
//           employmentRate: [88, 89, 91, 90, 92],
//           stayShanghaiRate: [52, 55, 57, 58, 60],
//         },
//         filters: {
//           year: '2025',
//           region: '上海',
//         },
//       })

//       setReport(res.data.report)
//     } catch (error) {
//       console.error(error)
//       setReport('报告生成失败，请检查后端服务是否启动。')
//     } finally {
//       setLoading(false)
//     }
//   }

//   return (
//     <Space orientation="vertical" style={{ width: '100%' }} size="large">
//       <Card title={<span style={titleStyle}>报告生成条件</span>} bordered={false} style={panelStyle}>
//         <TextArea
//           rows={6}
//           value={promptText}
//           onChange={(e) => setPromptText(e.target.value)}
//           style={{
//             background: '#081a2b',
//             color: '#d9eeff',
//             border: '1px solid #1b4f7d',
//           }}
//         />
//         <Button
//           type="primary"
//           onClick={handleGenerate}
//           loading={loading}
//           style={{
//             marginTop: 16,
//             background: 'linear-gradient(90deg, #0b6cff 0%, #14b8ff 100%)',
//             border: 'none',
//             fontWeight: 600,
//           }}
//         >
//           生成分析专报
//         </Button>
//       </Card>

//       <Card title={<span style={titleStyle}>专报内容</span>} bordered={false} style={panelStyle}>
//         <pre
//           style={{
//             whiteSpace: 'pre-wrap',
//             fontFamily: 'inherit',
//             lineHeight: 1.9,
//             color: '#d9eeff',
//             minHeight: 260,
//           }}
//         >
//           {report || '这里将显示自动生成的分析专报。'}
//         </pre>
//       </Card>
//     </Space>
//   )
// }

import { useState } from 'react'
import { Card, Input, Button, Space } from 'antd'
import axios from 'axios'

import employmentData from '../assets/mock/employment_summary.json'
import forecastData from '../assets/mock/salary_forecast.json'
import enrollmentData from '../assets/mock/enrollment_matching.json'
import rulesData from '../assets/mock/major_matching_rules.json'
import recommendationData from '../assets/mock/job_recommendation.json'
import { buildReportSummary } from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  inputStyle,
  primaryButtonStyle,
} from '../utils/uiTheme'

const { TextArea } = Input


export default function AIReport() {
  const [report, setReport] = useState('')
  const [loading, setLoading] = useState(false)
  const [promptText, setPromptText] = useState(
    '请基于动态监测、需求预测、招生匹配、培养优化、就业推荐五个模块，生成面向高校管理者的分析专报。'
  )

  const handleGenerate = async () => {
    try {
      setLoading(true)

      const res = await axios.post('http://127.0.0.1:5000/api/report/generate', {
        prompt: promptText,
        currentPage: 'report',
        chartData: {
        employmentRate: [88, 89, 91, 90, 92],
        stayShanghaiRate: [52, 55, 57, 58, 60]
      },
      filters: {
        year: '2025',
        region: '上海'
      }
    })

    setReport(res.data.report)
  } catch (error) {
    console.error(error)
    setReport('报告生成失败，请检查 Flask 后端是否启动。')
  } finally {
    setLoading(false)
  }
}

  return (
    <Space orientation="vertical" style={{ width: '100%' }} size="large">
      <Card title={<span style={sectionTitleStyle}>报告生成条件</span>} bordered={false} style={panelStyle}>
        <TextArea
        rows={6}
        value={promptText}
        onChange={(e) => setPromptText(e.target.value)}
        style={inputStyle}
        />
        <Button
        type="primary"
        onClick={handleGenerate}
        loading={loading}
        style={{ marginTop: 16, ...primaryButtonStyle }}
        >
          生成分析专报
        </Button>
      </Card>

      <Card title={<span style={sectionTitleStyle}>专报内容</span>} bordered={false} style={panelStyle}>
        <pre
          style={{
            whiteSpace: 'pre-wrap',
            fontFamily: 'inherit',
            lineHeight: 1.9,
            color: '#d9eeff',
            minHeight: 260,
          }}
        >
          {report || '这里将显示自动生成的分析专报。'}
        </pre>
      </Card>
    </Space>
  )
}