import React from 'react'

import { useAccount, useMsal } from '@azure/msal-react'
import { Layout } from 'antd'

import HeaderWidget from './headerWidget'

import styles from './index.module.less'

const Header = () => {
  const userName = window.localStorage.getItem('user_name') as string
  console.log(userName)
  return (
    <>
      <Layout.Header className={styles.header}>
        <span></span>
        <span className={styles.right}>
          <HeaderWidget username={userName} />
        </span>
      </Layout.Header>
      <div className={styles.vacancy} />
    </>
  )
}

export default Header
