import { Component } from 'react'
import { Card } from 'antd'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    console.error('页面渲染异常，请检查控制台错误信息', error, info?.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card>
          页面渲染异常，请检查控制台错误信息
        </Card>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
