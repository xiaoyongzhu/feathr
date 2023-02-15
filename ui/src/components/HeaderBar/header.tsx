import React from 'react'

import { useAccount, useMsal } from '@azure/msal-react'
import { Layout } from 'antd'

import HeaderWidget from './headerWidget'

import styles from './index.module.less'

const Header = () => {
  const { accounts } = useMsal()
  const account = useAccount(accounts[0] || {})
  const userName = window.localStorage.getItem('user_name')
  return (
    <>
      <Layout.Header className={styles.header}>
        <span></span>
        <span className={styles.right}>
          <HeaderWidget username={account?.username || userName || 'test 99999'} />
        </span>
      </Layout.Header>
      <div className={styles.vacancy} />
    </>
  )
}

export default Header
