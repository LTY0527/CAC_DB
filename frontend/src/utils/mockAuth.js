export const AUTH_STORAGE_KEY = 'cac_platform_session_v1'

const MOCK_ACCOUNTS = [
  {
    id: 'teacher-shu',
    username: 'teacher_shu',
    password: '123456',
    name: '\u5f20\u8001\u5e08',
    role: 'teacher',
    roleLabel: '\u5b66\u6821\u8001\u5e08',
    school: '\u4e0a\u6d77\u5927\u5b66',
    description: '\u9762\u5411\u672c\u6821\u4e13\u4e1a\u5efa\u8bbe\u3001\u57f9\u517b\u4f18\u5316\u548c\u62db\u751f\u8c03\u63a7\u7684\u6821\u5185\u89c6\u89d2\u3002',
  },
  {
    id: 'gov-sh',
    username: 'gov_sh',
    password: '123456',
    name: '\u5e02\u6559\u59d4\u4e13\u5458',
    role: 'gov',
    roleLabel: '\u653f\u5e9c\u4eba\u5458',
    school: '',
    description: '\u67e5\u770b\u5168\u5e02\u9ad8\u6821\u4e13\u4e1a\u5e03\u5c40\u3001\u4ea7\u4e1a\u5339\u914d\u548c\u7ed3\u6784\u8c03\u6574\u5efa\u8bae\u3002',
  },
  {
    id: 'public-guest',
    username: 'guest',
    password: '123456',
    name: '\u793e\u4f1a\u516c\u4f17',
    role: 'public',
    roleLabel: '\u793e\u4f1a\u516c\u4f17',
    school: '',
    description: '\u67e5\u770b\u9ad8\u6821\u4e13\u4e1a\u516c\u5f00\u4fe1\u606f\u3001\u5c31\u4e1a\u7ed3\u679c\u548c\u884c\u4e1a\u8d8b\u52bf\u3002',
  },
]

export function getMockAccounts() {
  return MOCK_ACCOUNTS.map((account) => {
    const session = { ...account }
    delete session.password
    return session
  })
}

export function loginWithMockAccount(username, password) {
  const account = MOCK_ACCOUNTS.find(
    (item) => item.username === String(username).trim() && item.password === String(password)
  )

  if (!account) return null

  const session = { ...account }
  delete session.password
  return session
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
