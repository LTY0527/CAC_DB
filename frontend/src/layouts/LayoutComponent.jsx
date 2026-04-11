import { useEffect } from 'react'
import { Button, Layout, Menu, Space, Tag } from 'antd'
import { LogoutOutlined, UserOutlined } from '@ant-design/icons'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ROLE_CONFIGS } from '../config/roleConfig.jsx'
import { useAuth } from '../context/AuthContext'
import usePlatformData from '../hooks/usePlatformData'
import { logModuleAccess } from '../services/dataService'
import { designTokens } from '../utils/uiTheme'

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
  const allSchools = Array.from(new Set((platformData.employmentData || []).map((item) => item.school_name).filter(Boolean)))
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

  useEffect(() => {
    if (!session?.token) return
    logModuleAccess({
      module_name: location.pathname,
      target_type: 'ROUTE',
      target_id: location.pathname,
      message: `view:${location.pathname}`,
    }).catch(() => {
      // access log should not block page rendering
    })
  }, [location.pathname, session?.token])

  return (
    <Layout style={{ minHeight: '100vh', background: 'transparent' }}>
      <Sider
        width={264}
        theme="light"
        style={{
          background: 'rgba(255,255,255,0.78)',
          borderRight: `1px solid ${designTokens.border}`,
          boxShadow: 'inset -1px 0 0 rgba(148, 163, 184, 0.08)',
          backdropFilter: 'blur(12px)',
        }}
      >
        <div style={{ padding: '24px 20px 18px', borderBottom: `1px solid ${designTokens.border}` }}>
          <div style={{ color: designTokens.textPrimary, fontSize: 21, fontWeight: 700, letterSpacing: '-0.01em', lineHeight: 1.35 }}>
            {roleConfig.title}
          </div>
          <div style={{ marginTop: 8, color: designTokens.textMuted, fontSize: 12, lineHeight: 1.7 }}>
            {roleConfig.subtitle}
          </div>
        </div>

        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={({ key }) => navigate(key)}
          inlineIndent={16}
          style={{
            marginTop: 14,
            padding: '0 14px',
            borderInlineEnd: 'none',
          }}
          items={roleConfig.menuItems}
        />
      </Sider>

      <Layout style={{ background: 'transparent' }}>
        <Header
          style={{
            height: 88,
            padding: '10px 24px',
            background: 'rgba(255,255,255,0.68)',
            backdropFilter: 'blur(12px)',
            borderBottom: `1px solid ${designTokens.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', minHeight: 56 }}>
            <div style={{ color: designTokens.textPrimary, fontSize: 24, fontWeight: 700, lineHeight: 1.25, letterSpacing: '-0.02em' }}>
              {roleConfig.headerTitle(currentSchool)}
            </div>
            <div style={{ marginTop: 6, color: designTokens.textMuted, fontSize: 12, lineHeight: 1.6 }}>
              {roleConfig.headerSubtitle}
            </div>
          </div>

          <Space size={10} align="start">
            <div
              style={{
                padding: '10px 12px',
                borderRadius: 14,
                background: 'rgba(255,255,255,0.76)',
                border: `1px solid ${designTokens.border}`,
                minWidth: 230,
              }}
            >
              <Space wrap size={[8, 8]}>
                <Tag color="processing" icon={<UserOutlined />}>
                  {session?.name}
                </Tag>
                <Tag color="blue">{roleConfig.label}</Tag>
                {session?.school ? <Tag color="default">{session.school}</Tag> : null}
              </Space>
            </div>
            <Tag color="blue">数据版本：V2.0</Tag>
            <Tag color={platformData.loading ? 'gold' : platformData.error ? 'red' : 'green'}>
              {platformData.loading ? '状态：数据加载中' : platformData.error ? '状态：部分数据异常' : '状态：数据已连接'}
            </Tag>
            <Button
              icon={<LogoutOutlined />}
              onClick={async () => {
                await logout()
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
