import React from 'react'

import { Button, Result } from 'antd'

import styles from './index.module.less'

const App: React.FC = () => {
  const goLogin = () => {
    window.location.href = '/login'
  }
  return (
    <div className={styles.containerBox}>
      <Result
        extra={
          <Button key="console" type="primary" onClick={goLogin}>
            Login
          </Button>
        }
        status="warning"
        title="You haven't joined the organization yet."
      />
    </div>
  )
}

export default App
