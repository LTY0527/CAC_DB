import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Button, Card, Col, Input, Row, Space, Tag, message } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'
import { getDefaultPathByRole } from '../config/roleConfig.jsx'

const TEXT = {
  platformTag: '高校人才培养与就业大数据平台',
  loginTitle: '进入平台',
  loginDesc: '使用数据库中的演示账号登录，系统会根据角色自动加载对应视图与菜单。',
  username: '账号',
  password: '密码',
  usernamePlaceholder: '请输入账号',
  passwordPlaceholder: '请输入密码',
  loginBtn: '登录并进入系统',
  loginError: '账号或密码错误，或账户暂时不可用，请稍后重试。',
}

const ROLE_COLORS = {
  teacher: 'blue',
  government: 'cyan',
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
  border: '1px solid rgba(125, 159, 197, 0.18)',
  boxShadow: '0 28px 70px rgba(0, 0, 0, 0.34)',
  background:
    'linear-gradient(135deg, rgba(7, 20, 36, 0.98) 0%, rgba(9, 25, 42, 0.99) 52%, rgba(8, 18, 32, 0.99) 100%)',
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { accounts, login } = useAuth()
  const [username, setUsername] = useState(accounts[0]?.username || '')
  const [password, setPassword] = useState('')
  const [activeAccount, setActiveAccount] = useState(accounts[0]?.id || '')
  const [submitting, setSubmitting] = useState(false)

  const redirectPath = location.state?.from

  const handleLogin = async () => {
    setSubmitting(true)
    try {
      const session = await login(username, password)
      if (!session) {
        message.error(TEXT.loginError)
        return
      }

      navigate(redirectPath || getDefaultPathByRole(session.role), { replace: true })
    } catch (error) {
      message.error(error?.response?.data?.message || TEXT.loginError)
    } finally {
      setSubmitting(false)
    }
  }

  const fillAccount = (account) => {
    setUsername(account.username)
    setPassword('')
    setActiveAccount(account.id)
  }

  return (
    <div style={shellStyle} className="login-shell">
      <div style={panelStyle} className="login-surface">
        <div style={{ padding: '34px 36px 10px' }}>
          <Tag
            color="processing"
            style={{
              borderRadius: 999,
              paddingInline: 12,
              marginBottom: 14,
              fontWeight: 600,
              background: 'rgba(22, 119, 255, 0.14)',
              borderColor: 'rgba(103, 180, 255, 0.34)',
              color: '#e6f4ff',
            }}
          >
            {TEXT.platformTag}
          </Tag>
        </div>

        <Row gutter={[24, 24]} style={{ padding: '0 36px 36px' }}>
          <Col xs={24} xl={10}>
            <Card bordered={false} className="login-panel-card">
              <div style={{ color: '#f8fbff', fontSize: 30, fontWeight: 700, letterSpacing: '-0.02em' }}>
                {TEXT.loginTitle}
              </div>
              <div style={{ marginTop: 10, color: 'rgba(225, 236, 248, 0.88)', lineHeight: 1.85, fontSize: 14 }}>
                {TEXT.loginDesc}
              </div>

              <Space direction="vertical" size="middle" style={{ width: '100%', marginTop: 24 }}>
                <div>
                  <div style={{ color: '#edf6ff', marginBottom: 8, fontSize: 13, fontWeight: 600 }}>
                    {TEXT.username}
                  </div>
                  <Input
                    prefix={<UserOutlined style={{ color: '#64748b' }} />}
                    size="large"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder={TEXT.usernamePlaceholder}
                    className="login-input"
                  />
                </div>

                <div>
                  <div style={{ color: '#edf6ff', marginBottom: 8, fontSize: 13, fontWeight: 600 }}>
                    {TEXT.password}
                  </div>
                  <Input.Password
                    prefix={<LockOutlined style={{ color: '#64748b' }} />}
                    size="large"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    onPressEnter={handleLogin}
                    placeholder={TEXT.passwordPlaceholder}
                    className="login-input"
                  />
                </div>

                <Button
                  type="primary"
                  size="large"
                  onClick={handleLogin}
                  className="login-submit-btn"
                  loading={submitting}
                >
                  {TEXT.loginBtn}
                </Button>
              </Space>
            </Card>
          </Col>

          <Col xs={24} xl={14}>
            <Row gutter={[16, 16]}>
              {accounts.map((account) => {
                const selected = activeAccount === account.id
                return (
                  <Col xs={24} md={12} xl={8} key={account.id}>
                    <Card
                      bordered={false}
                      hoverable
                      onClick={() => fillAccount(account)}
                      className={`login-account-card${selected ? ' is-selected' : ''}`}
                    >
                      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Space wrap>
                          <Tag color={ROLE_COLORS[account.role]}>{account.roleLabel}</Tag>
                          {account.school ? <Tag color="geekblue">{account.school}</Tag> : null}
                          {selected ? <Tag color="processing">当前选中</Tag> : null}
                        </Space>
                        <div style={{ color: '#f5f9ff', fontSize: 20, fontWeight: 700 }}>{account.name}</div>
                        <div style={{ color: 'rgba(223, 236, 248, 0.92)', fontSize: 13 }}>账号：{account.username}</div>
                        <div style={{ color: 'rgba(214, 231, 249, 0.82)', lineHeight: 1.75, fontSize: 13 }}>
                          {account.description}
                        </div>
                      </Space>
                    </Card>
                  </Col>
                )
              })}
            </Row>
          </Col>
        </Row>
      </div>
    </div>
  )
}
