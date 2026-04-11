export const AUTH_STORAGE_KEY = 'cac_platform_session_v2'

const DEMO_ACCOUNTS = [
  {
    id: 'teacher-shu',
    username: 'teacher_shu',
    name: '张老师',
    role: 'teacher',
    roleLabel: '学校教师',
    school: '上海大学',
    description: '面向本校专业建设、培养优化和招生调控的校内视角。',
  },
  {
    id: 'gov-sh',
    username: 'gov_sh',
    name: '市教委专员',
    role: 'government',
    roleLabel: '政府人员',
    school: '',
    description: '查看全市高校专业布局、产业匹配和结构调整建议。',
  },
  {
    id: 'public-guest',
    username: 'guest',
    name: '社会公众',
    role: 'public',
    roleLabel: '社会公众',
    school: '',
    description: '查看高校专业公开信息、就业结果和行业趋势。',
  },
]

export function getDemoAccounts() {
  return DEMO_ACCOUNTS
}

export function getStoredSession() {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

export function storeSession(session) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function clearStoredSession() {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}
