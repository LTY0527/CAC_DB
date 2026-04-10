export const designTokens = {
  pageBg: '#f4f7fb',
  pageBgAccent: '#eef3f8',
  surface: '#ffffff',
  surfaceAlt: '#f8fafc',
  surfaceMuted: '#f1f5f9',
  textPrimary: '#0f172a',
  textSecondary: '#475569',
  textMuted: '#64748b',
  border: '#e2e8f0',
  borderStrong: '#cbd5e1',
  shadow: '0 12px 28px rgba(15, 23, 42, 0.06)',
  shadowSoft: '0 6px 18px rgba(15, 23, 42, 0.04)',
  accent: '#2563eb',
  accentSoft: '#dbeafe',
  accentSecondary: '#0f766e',
  success: '#16a34a',
  successSoft: '#dcfce7',
  danger: '#dc2626',
  dangerSoft: '#fee2e2',
  warning: '#d97706',
  warningSoft: '#fef3c7',
  purple: '#6366f1',
  purpleSoft: '#e0e7ff',
}

export const chartPalette = ['#2563eb', '#4f46e5', '#0f766e', '#0891b2', '#64748b', '#1d4ed8', '#0ea5e9', '#7c3aed', '#059669', '#475569']
export const chartPositive = '#16a34a'
export const chartNegative = '#dc2626'

export const axisLabelStyle = { color: designTokens.textMuted, fontSize: 12 }
export const axisLineStyle = { lineStyle: { color: designTokens.borderStrong } }
export const splitLineStyle = { lineStyle: { color: 'rgba(148, 163, 184, 0.18)' } }
export const legendTextStyle = { color: designTokens.textSecondary, fontSize: 12 }

export const panelStyle = {
  background: designTokens.surface,
  border: `1px solid ${designTokens.border}`,
  borderRadius: 16,
  boxShadow: designTokens.shadowSoft,
  overflow: 'hidden',
}

export const sectionTitleStyle = {
  color: designTokens.textPrimary,
  fontSize: 17,
  fontWeight: 700,
  letterSpacing: '-0.01em',
}

export const statTitleStyle = {
  color: designTokens.textMuted,
  fontSize: 13,
  fontWeight: 500,
}

const statBase = {
  fontSize: 34,
  fontWeight: 700,
  letterSpacing: '-0.02em',
}

export const statValuePrimary = {
  ...statBase,
  color: designTokens.textPrimary,
}

export const statValueBlue = {
  ...statBase,
  color: designTokens.accent,
}

export const statValueCyan = {
  ...statBase,
  color: '#0f766e',
}

export const statValuePurple = {
  ...statBase,
  color: designTokens.purple,
}

export const darkTooltip = {
  backgroundColor: 'rgba(255, 255, 255, 0.98)',
  borderColor: designTokens.border,
  borderWidth: 1,
  textStyle: { color: designTokens.textPrimary, fontSize: 12 },
  extraCssText: `box-shadow:${designTokens.shadow};border-radius:12px;padding:10px 12px;`,
}

export const inputStyle = {
  background: designTokens.surface,
  color: designTokens.textPrimary,
  border: `1px solid ${designTokens.border}`,
  borderRadius: 10,
  boxShadow: 'none',
}

export const primaryButtonStyle = {
  height: 36,
  padding: '0 16px',
  borderRadius: 10,
  fontSize: 14,
  fontWeight: 600,
  background: designTokens.accent,
  border: 'none',
  color: '#ffffff',
  boxShadow: '0 6px 16px rgba(37, 99, 235, 0.18)',
}

export const secondaryButtonStyle = {
  height: 36,
  padding: '0 16px',
  borderRadius: 10,
  fontSize: 14,
  fontWeight: 600,
  background: designTokens.surface,
  border: `1px solid ${designTokens.border}`,
  color: designTokens.textSecondary,
}

export const noteTextStyle = {
  color: designTokens.textSecondary,
  lineHeight: 1.8,
  fontSize: 14,
}

export const metaLabelStyle = {
  color: designTokens.textMuted,
  fontSize: 11,
  textTransform: 'uppercase',
  letterSpacing: 0.7,
}

export const metaValueStyle = {
  color: designTokens.textPrimary,
  fontSize: 14,
  lineHeight: 1.7,
  fontWeight: 500,
}

export const riskTextStyle = {
  color: designTokens.warning,
  lineHeight: 1.75,
  fontSize: 13,
}

export const algorithmTextStyle = {
  color: designTokens.textSecondary,
  lineHeight: 1.75,
  fontSize: 13,
}

export const antdTheme = {
  token: {
    colorPrimary: designTokens.accent,
    colorSuccess: designTokens.success,
    colorError: designTokens.danger,
    colorWarning: designTokens.warning,
    colorInfo: designTokens.accent,
    colorText: designTokens.textPrimary,
    colorTextSecondary: designTokens.textSecondary,
    colorTextTertiary: designTokens.textMuted,
    colorBorder: designTokens.border,
    colorBorderSecondary: designTokens.border,
    colorBgBase: designTokens.pageBg,
    colorBgContainer: designTokens.surface,
    colorBgElevated: designTokens.surface,
    colorFillAlter: designTokens.surfaceMuted,
    colorFillTertiary: designTokens.surfaceMuted,
    borderRadius: 12,
    borderRadiusLG: 16,
    boxShadowSecondary: designTokens.shadow,
    fontFamily: '"PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif',
  },
  components: {
    Layout: {
      bodyBg: 'transparent',
      headerBg: 'transparent',
      siderBg: 'transparent',
      triggerBg: designTokens.surface,
    },
    Card: {
      headerBg: designTokens.surface,
      colorBorderSecondary: designTokens.border,
      paddingLG: 20,
    },
    Statistic: {
      contentFontSize: 34,
    },
    Menu: {
      itemBg: 'transparent',
      itemColor: designTokens.textSecondary,
      itemHoverColor: designTokens.textPrimary,
      itemSelectedColor: designTokens.accent,
      itemSelectedBg: designTokens.accentSoft,
      darkItemBg: 'transparent',
      darkItemColor: designTokens.textSecondary,
      darkItemSelectedBg: designTokens.accentSoft,
      darkItemSelectedColor: designTokens.accent,
      darkSubMenuItemBg: 'transparent',
    },
    Table: {
      headerBg: designTokens.surfaceAlt,
      headerColor: designTokens.textSecondary,
      colorText: designTokens.textPrimary,
      colorTextHeading: designTokens.textPrimary,
      rowHoverBg: '#f8fbff',
      borderColor: designTokens.border,
    },
    Select: {
      controlHeight: 38,
      optionSelectedBg: designTokens.accentSoft,
      optionActiveBg: '#eff6ff',
    },
    Input: {
      controlHeight: 38,
      activeBorderColor: designTokens.accent,
      hoverBorderColor: '#93c5fd',
    },
    Button: {
      controlHeight: 36,
      borderRadius: 10,
      defaultBorderColor: designTokens.border,
      defaultColor: designTokens.textSecondary,
      defaultBg: designTokens.surface,
      primaryShadow: '0 6px 16px rgba(37, 99, 235, 0.18)',
    },
    Segmented: {
      itemColor: designTokens.textSecondary,
      itemSelectedColor: designTokens.accent,
      itemSelectedBg: designTokens.surface,
      trackBg: designTokens.surfaceMuted,
    },
    Tag: {
      borderRadiusSM: 999,
    },
    Empty: {
      colorTextDescription: designTokens.textMuted,
    },
  },
}
