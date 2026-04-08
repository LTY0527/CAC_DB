import { Button, Layout, Menu, Space, Tag } from 'antd'
import { LogoutOutlined, UserOutlined } from '@ant-design/icons'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ROLE_CONFIGS } from '../config/roleConfig.jsx'
import { useAuth } from '../context/AuthContext'
import usePlatformData from '../hooks/usePlatformData'

const { Header, Sider, Content } = Layout

function getSelectedMenuKey(pathname, menuItems) {
  const match = menuItems.find((item) => pathname.startsWith(item.key))
  return match?.key || menuItems[0]?.key
}

export default function LayoutComponent() {
  const navigate = useNavigate()
  const location = useLocation()
  const { session, logout } = useAuth()
  const platformData = usePlatformData()

  const roleConfig = ROLE_CONFIGS[session?.role] || ROLE_CONFIGS.teacher
  const allSchools = Array.from(
    new Set((platformData.employmentData || []).map((item) => item.school_name).filter(Boolean))
  )
  const currentSchool =
    session?.role === 'teacher' && session?.school
      ? session.school
      : (allSchools.includes('上海大学') ? '上海大学' : (allSchools[0] || '上海大学'))

  const selectedKey = getSelectedMenuKey(location.pathname, roleConfig.menuItems)
  const outletContext = {
    ...platformData,
    currentSchool,
    roleMode: session?.role === 'teacher' ? 'school' : session?.role === 'gov' ? 'gov' : 'public',
  }

  return (
    <Layout style={{ minHeight: '100vh', background: 'linear-gradient(180deg, #08111b 0%, #0b1622 100%)' }}>
      <Sider
        width={248}
        theme="dark"
        style={{
          background: 'linear-gradient(180deg, #0b1622 0%, #0d1826 100%)',
          borderRight: '1px solid rgba(120, 160, 200, 0.14)',
          boxShadow: '8px 0 24px rgba(0, 0, 0, 0.18)',
        }}
      >
        <div style={{ padding: '22px 18px 18px', borderBottom: '1px solid rgba(120, 160, 200, 0.16)' }}>
          <div style={{ color: '#f3f7ff', fontSize: 22, fontWeight: 700, letterSpacing: 0.5, lineHeight: 1.4 }}>
            {roleConfig.title}
          </div>
          <div style={{ marginTop: 8, color: 'rgba(210, 225, 245, 0.68)', fontSize: 12, lineHeight: 1.7 }}>
            {roleConfig.subtitle}
          </div>
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={({ key }) => navigate(key)}
          inlineIndent={16}
          style={{
            background: 'transparent',
            color: '#cfe0f5',
            marginTop: 14,
            padding: '0 10px',
            borderInlineEnd: 'none',
          }}
          items={roleConfig.menuItems}
        />
      </Sider>

      <Layout style={{ background: 'transparent' }}>
        <Header
          style={{
            height: 96,
            padding: '8px 24px',
            background: 'rgba(10, 18, 28, 0.72)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(120, 160, 200, 0.14)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', minHeight: 64 }}>
            <div style={{ color: '#eef4ff', fontSize: 24, fontWeight: 700, lineHeight: 1.25 }}>
              {roleConfig.headerTitle(currentSchool)}
            </div>
            <div style={{ marginTop: 6, color: 'rgba(210, 225, 245, 0.64)', fontSize: 12, lineHeight: 1.6 }}>
              {roleConfig.headerSubtitle}
            </div>
          </div>

          <Space size={10} align="start">
            <div
              style={{
                padding: '10px 12px',
                borderRadius: 14,
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(120, 160, 200, 0.14)',
                minWidth: 230,
              }}
            >
              <Space wrap size={[8, 8]}>
                <Tag color="processing" icon={<UserOutlined />}>
                  {session?.name}
                </Tag>
                <Tag color="blue">{roleConfig.label}</Tag>
                {session?.school ? <Tag color="geekblue">{session.school}</Tag> : null}
              </Space>
            </div>
            <Tag color="blue">数据版本：v2.0</Tag>
            <Tag color={platformData.loading ? 'gold' : platformData.error ? 'red' : 'cyan'}>
              {platformData.loading ? '状态：数据加载中' : platformData.error ? '状态：数据异常' : '状态：平台数据已连接'}
            </Tag>
            <Button
              icon={<LogoutOutlined />}
              onClick={() => {
                logout()
                navigate('/login', { replace: true })
              }}
            >
              退出登录
            </Button>
          </Space>
        </Header>

        <Content style={{ margin: '24px 20px 20px', padding: 0, background: 'transparent' }}>
          <Outlet context={outletContext} />
        </Content>
      </Layout>
    </Layout>
  )
}
