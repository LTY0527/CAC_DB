// import { Layout, Menu } from 'antd'
// import { useState } from 'react'
// import Dashboard from './pages/Dashboard'
// import RuleAnalysis from './pages/RuleAnalysis'
// import AIReport from './pages/AIReport'

// const { Header, Sider, Content } = Layout

// export default function App() {
//   const [current, setCurrent] = useState('dashboard')

//   const renderPage = () => {
//     if (current === 'dashboard') return <Dashboard />
//     if (current === 'rules') return <RuleAnalysis />
//     if (current === 'report') return <AIReport />
//     return <Dashboard />
//   }

//   return (
//     <Layout style={{ minHeight: '100vh', background: '#061522' }}>
//       <Sider
//         width={230}
//         theme="dark"
//         style={{
//           background: 'linear-gradient(180deg, #03162a 0%, #02111f 100%)',
//           borderRight: '1px solid #123b63',
//           boxShadow: '0 0 16px rgba(0, 153, 255, 0.12)',
//         }}
//       >
//         <div
//           style={{
//             color: '#d8f0ff',
//             padding: '22px 18px',
//             fontSize: 24,
//             fontWeight: 700,
//             letterSpacing: 1,
//             textAlign: 'center',
//             borderBottom: '1px solid #123b63',
//             textShadow: '0 0 8px rgba(55, 170, 255, 0.35)',
//           }}
//         >
//           高校就业分析平台
//         </div>

//         <Menu
//           theme="dark"
//           mode="inline"
//           selectedKeys={[current]}
//           onClick={({ key }) => setCurrent(key)}
//           style={{
//             background: 'transparent',
//             color: '#b7dfff',
//             marginTop: 10,
//             borderInlineEnd: 'none',
//           }}
//           items={[
//             { key: 'dashboard', label: '总览看板' },
//             { key: 'rules', label: '关联规则分析' },
//             { key: 'report', label: '分析专报' },
//           ]}
//         />
//       </Sider>

//       <Layout style={{ background: '#061522' }}>
//         <Header
//           style={{
//             background: 'linear-gradient(90deg, #071a2f 0%, #0a2742 50%, #071a2f 100%)',
//             color: '#e6f4ff',
//             fontSize: 24,
//             fontWeight: 700,
//             textAlign: 'center',
//             borderBottom: '1px solid #123b63',
//             boxShadow: '0 2px 14px rgba(0, 102, 255, 0.16)',
//             letterSpacing: 1,
//           }}
//         >
//           高校就业与留沪数据分析平台
//         </Header>

//         <Content
//           style={{
//             margin: 16,
//             padding: 4,
//             background: '#061522',
//           }}
//         >
//           {renderPage()}
//         </Content>
//       </Layout>
//     </Layout>
//   )
// }

import { Layout, Menu, Tag, Space } from 'antd'
import {
  DashboardOutlined,
  LineChartOutlined,
  BarChartOutlined,
  ApartmentOutlined,
  ReadOutlined,
  ThunderboltOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import EmploymentMonitor from './pages/EmploymentMonitor'
import SalaryForecast from './pages/SalaryForecast'
import EnrollmentMatching from './pages/EnrollmentMatching'
import RuleAnalysis from './pages/RuleAnalysis'
import JobRecommendation from './pages/JobRecommendation'
import AIReport from './pages/AIReport'

const { Header, Sider, Content } = Layout

export default function App() {
  const [current, setCurrent] = useState('dashboard')

  const renderPage = () => {
    switch (current) {
      case 'dashboard':
        return <Dashboard />
      case 'employment':
        return <EmploymentMonitor />
      case 'forecast':
        return <SalaryForecast />
      case 'enrollment':
        return <EnrollmentMatching />
      case 'rules':
        return <RuleAnalysis />
      case 'recommendation':
        return <JobRecommendation />
      case 'report':
        return <AIReport />
      default:
        return <Dashboard />
    }
  }

  return (
    <Layout
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #08111b 0%, #0b1622 100%)',
      }}
    >
      <Sider
        width={248}
        theme="dark"
        style={{
          background: 'linear-gradient(180deg, #0b1622 0%, #0d1826 100%)',
          borderRight: '1px solid rgba(120, 160, 200, 0.14)',
          boxShadow: '8px 0 24px rgba(0, 0, 0, 0.18)',
        }}
      >
        <div
          style={{
            padding: '22px 18px 18px',
            borderBottom: '1px solid rgba(120, 160, 200, 0.16)',
          }}
        >
          <div
            style={{
              color: '#f3f7ff',
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: 0.5,
              lineHeight: 1.4,
            }}
          >
            高校就业分析平台
          </div>

          <div
            style={{
              marginTop: 8,
              color: 'rgba(210, 225, 245, 0.68)',
              fontSize: 12,
              lineHeight: 1.7,
            }}
          >
            就业监测 · 招生匹配 · 培养优化 · AI专报
          </div>
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[current]}
          onClick={({ key }) => setCurrent(key)}
          inlineIndent={16}
          style={{
            background: 'transparent',
            color: '#cfe0f5',
            marginTop: 14,
            padding: '0 10px',
            borderInlineEnd: 'none',
          }}
          items={[
            { key: 'dashboard', icon: <DashboardOutlined />, label: '总览看板' },
            { key: 'employment', icon: <LineChartOutlined />, label: '动态监测' },
            { key: 'forecast', icon: <BarChartOutlined />, label: '需求预测' },
            { key: 'enrollment', icon: <ApartmentOutlined />, label: '招生匹配' },
            { key: 'rules', icon: <ThunderboltOutlined />, label: '培养优化' },
            { key: 'recommendation', icon: <ReadOutlined />, label: '就业推荐' },
            { key: 'report', icon: <FileTextOutlined />, label: '分析专报' },
          ]}
        />
      </Sider>

      <Layout style={{ background: 'transparent' }}>
        <Header
          style={{
            height: 80,
            padding: '6px 24px 0',
            background: 'rgba(10, 18, 28, 0.72)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(120, 160, 200, 0.14)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div
              style={{
                color: '#eef4ff',
                fontSize: 24,
                fontWeight: 700,
                lineHeight: 1.2,
                marginTop: 40,
              }}
            >
              高校就业与招生联动分析平台
            </div>
            <div
              style={{
                marginTop: 4,
                color: 'rgba(210, 225, 245, 0.64)',
                fontSize: 12,
              }}
            >
              面向高校管理场景的数据监测与辅助决策平台
            </div>
          </div>

          <Space size={10}>
            <Tag color="blue">数据版本：V1.0</Tag>
            <Tag color="cyan">状态：已连接 Mock 数据</Tag>
          </Space>
        </Header>

        <Content
          style={{
            margin: 20,
            padding: 0,
            background: 'transparent',
          }}
        >
          {renderPage()}
        </Content>
      </Layout>
    </Layout>
  )
}