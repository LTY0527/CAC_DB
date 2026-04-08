import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Button, Card, Col, Input, Row, Space, Tag, message } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'
import { getDefaultPathByRole } from '../config/roleConfig.jsx'

const TEXT = {
  platformTag: '基于大数据高校“需求-招生一培养一就业一监测”一体化平台',
  loginTitle: '进入平台',
  loginDesc: '使用演示账号登录，系统会根据角色自动加载对应视图与菜单。',
  username: '账号',
  password: '密码',
  usernamePlaceholder: '请输入账号',
  passwordPlaceholder: '请输入密码',
  loginBtn: '登录并进入系统',
  loginError: '账号或密码不正确，请使用下方演示账号登录。',
}

const ROLE_COLORS = {
  teacher: 'blue',
  gov: 'cyan',
  public: 'green',
}

const shellStyle = {
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '32px 20px',
  background:
    'radial-gradient(circle at top left, rgba(56, 123, 255, 0.18), transparent 28%), radial-gradient(circle at right, rgba(44, 205, 255, 0.14), transparent 24%), linear-gradient(180deg, #07111d 0%, #091827 100%)',
}

const panelStyle = {
  width: 'min(980px, 100%)',
  borderRadius: 28,
  overflow: 'hidden',
  border: '1px solid rgba(117, 159, 198, 0.16)',
  boxShadow: '0 26px 60px rgba(0, 0, 0, 0.28)',
  background:
    'linear-gradient(135deg, rgba(7, 20, 36, 0.96) 0%, rgba(9, 25, 42, 0.98) 52%, rgba(9, 19, 34, 0.98) 100%)',
}

const loginCardStyle = {
  background:
    'linear-gradient(180deg, rgba(11, 32, 56, 0.96) 0%, rgba(9, 24, 42, 0.96) 100%)',
  border: '1px solid rgba(117, 159, 198, 0.15)',
  borderRadius: 24,
}

const accountCardStyle = {
  minHeight: 156,
  borderRadius: 18,
  background:
    'linear-gradient(180deg, rgba(8, 24, 42, 0.92) 0%, rgba(7, 19, 32, 0.95) 100%)',
  border: '1px solid rgba(117, 159, 198, 0.12)',
  cursor: 'pointer',
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { accounts, login } = useAuth()
  const [username, setUsername] = useState(accounts[0]?.username || '')
  const [password, setPassword] = useState('123456')
  const [activeAccount, setActiveAccount] = useState(accounts[0]?.id || '')

  const redirectPath = location.state?.from

  const handleLogin = () => {
    const session = login(username, password)
    if (!session) {
      message.error(TEXT.loginError)
      return
    }

    navigate(redirectPath || getDefaultPathByRole(session.role), { replace: true })
  }

  const fillAccount = (account) => {
    setUsername(account.username)
    setPassword('123456')
    setActiveAccount(account.id)
  }

  return (
    <div style={shellStyle}>
      <div style={panelStyle}>
        <div style={{ padding: '34px 36px 10px' }}>
          <Tag color="processing" style={{ borderRadius: 999, paddingInline: 12, marginBottom: 14 }}>
            {TEXT.platformTag}
          </Tag>
        </div>

        <Row gutter={[24, 24]} style={{ padding: '0 36px 36px' }}>
          <Col xs={24} xl={10}>
            <Card bordered={false} style={loginCardStyle}>
              <div style={{ color: '#f0f6ff', fontSize: 28, fontWeight: 700 }}>{TEXT.loginTitle}</div>
              <div style={{ marginTop: 8, color: 'rgba(214, 231, 249, 0.66)', lineHeight: 1.8 }}>
                {TEXT.loginDesc}
              </div>

              <Space direction="vertical" size="middle" style={{ width: '100%', marginTop: 22 }}>
                <div>
                  <div style={{ color: '#d7ebff', marginBottom: 8, fontSize: 13 }}>{TEXT.username}</div>
                  <Input
                    prefix={<UserOutlined style={{ color: '#7cb8de' }} />}
                    size="large"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder={TEXT.usernamePlaceholder}
                  />
                </div>

                <div>
                  <div style={{ color: '#d7ebff', marginBottom: 8, fontSize: 13 }}>{TEXT.password}</div>
                  <Input.Password
                    prefix={<LockOutlined style={{ color: '#7cb8de' }} />}
                    size="large"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    onPressEnter={handleLogin}
                    placeholder={TEXT.passwordPlaceholder}
                  />
                </div>

                <Button
                  type="primary"
                  size="large"
                  onClick={handleLogin}
                  style={{
                    height: 46,
                    marginTop: 8,
                    borderRadius: 14,
                    fontWeight: 700,
                    background:
                      'linear-gradient(90deg, rgba(35, 113, 255, 1) 0%, rgba(49, 202, 255, 1) 100%)',
                    border: 'none',
                  }}
                >
                  {TEXT.loginBtn}
                </Button>
              </Space>
            </Card>
          </Col>

          <Col xs={24} xl={14}>
            <Row gutter={[16, 16]}>
              {accounts.map((account) => (
                <Col xs={24} md={12} xl={8} key={account.id}>
                  <Card
                    bordered={false}
                    hoverable
                    onClick={() => fillAccount(account)}
                    style={{
                      ...accountCardStyle,
                      outline:
                        activeAccount === account.id
                          ? '1px solid rgba(70, 194, 255, 0.7)'
                          : 'none',
                    }}
                  >
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                      <Space wrap>
                        <Tag color={ROLE_COLORS[account.role]}>{account.roleLabel}</Tag>
                        {account.school ? <Tag color="geekblue">{account.school}</Tag> : null}
                      </Space>
                      <div style={{ color: '#f0f6ff', fontSize: 20, fontWeight: 700 }}>{account.name}</div>
                      <div style={{ color: 'rgba(214, 231, 249, 0.74)' }}>账号：{account.username}</div>
                      <div style={{ color: 'rgba(214, 231, 249, 0.64)', lineHeight: 1.8 }}>
                        {account.description}
                      </div>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </Col>
        </Row>
      </div>
    </div>
  )
}
