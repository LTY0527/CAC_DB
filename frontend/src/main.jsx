import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import App from './App'
import 'antd/dist/reset.css'
import './index.css'
import { antdTheme } from './utils/uiTheme'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConfigProvider theme={antdTheme}>
      <App />
    </ConfigProvider>
  </React.StrictMode>
)
