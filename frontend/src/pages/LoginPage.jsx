import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Button, Input, message } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'
import { getDefaultPathByRole } from '../config/roleConfig.jsx'
import './loginPage.css'

const TEXT = {
  platformTag: '高校人才培养与就业大数据平台',
  loginTitle: '进入平台',
  loginDesc: '使用演示账号登录，系统将根据角色自动进入对应工作界面。',
  username: '账号',
  password: '密码',
  usernamePlaceholder: '请输入账号',
  passwordPlaceholder: '请输入密码',
  loginBtn: '登录并进入系统',
  loginError: '账号或密码错误，或当前账号暂不可用，请稍后重试。',
}

const ROLE_ACCENT = {
  teacher: '#8f1d22',
  government: '#1677ff',
  public: '#0f766e',
}

const ROLE_LABEL = {
  teacher: '学校教师',
  government: '政府专员',
  public: '社会公众',
}

function AccountCard({ account, selected, onSelect }) {
  const accent = ROLE_ACCENT[account.role] || '#1677ff'

  return (
    <button
      type="button"
      className={`login-role-card${selected ? ' is-active' : ''}`}
      style={{
        '--card-accent': accent,
        '--card-bg': selected ? `${accent}0d` : '#ffffff',
      }}
      onClick={() => onSelect(account)}
    >
      <div className="login-role-card__body">
        <div className="login-role-card__top">
          <div className="login-role-card__role">{ROLE_LABEL[account.role] || account.roleLabel}</div>
          <div className="login-role-card__name">{account.name}</div>
          <div className="login-role-card__account">演示账号：{account.username}</div>
        </div>

        <div className="login-role-card__desc">{account.description}</div>

        <div className="login-role-card__footer">
          <div className="login-role-card__meta">
            <span className="login-role-card__meta-label">适用范围</span>
            <span className="login-role-card__meta-value">{account.school || '市级公开视角'}</span>
          </div>
        </div>
      </div>
    </button>
  )
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
  const selectedAccount = useMemo(
    () => accounts.find((item) => item.id === activeAccount) || accounts[0],
    [accounts, activeAccount]
  )

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
    <div className="login-page">
      <div className="login-page__shell">
        <section className="login-page__panel">
          <div className="login-page__intro">
            <div className="login-page__tag">{TEXT.platformTag}</div>
            <h1 className="login-page__title">{TEXT.loginTitle}</h1>
            <p className="login-page__desc">{TEXT.loginDesc}</p>
          </div>

          <div className="login-page__grid">
            <div className="login-page__form">
              <div className="login-page__section-title">账号登录</div>
              <div className="login-page__section-note">
                当前已选择：
                <span className="login-page__selected-name">{selectedAccount?.name || '-'}</span>
              </div>

              <div className="login-page__field">
                <label className="login-page__label">{TEXT.username}</label>
                <Input
                  prefix={<UserOutlined style={{ color: '#64748b' }} />}
                  size="large"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder={TEXT.usernamePlaceholder}
                  className="login-page__input"
                />
              </div>

              <div className="login-page__field">
                <label className="login-page__label">{TEXT.password}</label>
                <Input.Password
                  prefix={<LockOutlined style={{ color: '#64748b' }} />}
                  size="large"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  onPressEnter={handleLogin}
                  placeholder={TEXT.passwordPlaceholder}
                  className="login-page__input"
                />
              </div>

              <Button type="primary" size="large" loading={submitting} onClick={handleLogin} className="login-page__submit">
                {TEXT.loginBtn}
              </Button>
            </div>

            <div className="login-page__accounts">
              <div className="login-page__section-title">角色选择</div>
              <div className="login-page__section-note">选择角色后自动填入对应演示账号，右侧卡片按统一网格严格对齐。</div>

              <div className="login-page__cards-grid">
                {accounts.map((account) => (
                  <div key={account.id} className="login-page__card-cell">
                    <AccountCard account={account} selected={activeAccount === account.id} onSelect={fillAccount} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
