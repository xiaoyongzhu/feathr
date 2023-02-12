import React from 'react'

import { LockOutlined, UserOutlined, AlipayOutlined } from '@ant-design/icons'
import { Button, Checkbox, Form, Input, Row, Col, message } from 'antd'
import Cookies from 'js-cookie'

import { login } from '@/api'
import { LoginModel } from '@/models/model'

import styles from './index.module.less'

const App: React.FC = () => {
  const onFinish = (values: LoginModel) => {
    if (!values.email || !values.password) {
      return
    }
    login(values).then((response) => {
      let data = response.data
      if (data.status !== 'SUCCESS') {
        message.warning(response.data.message)
        return
      }
      data = data.data
      if (data.organizations.length === 0) {
        // todo: This user does not have any organizations, need redirect no organization page!
        return
      }
      message.success('Login Success')
      const token = data.token
      Cookies.set('token', token, {
        expires: 7
      })
      localStorage.setItem(
        'temp_organization_id',
        data?.organizations[0] ?? 'a1ccf112-3367-4c13-8c38-b4a8555497c2'
      )
      localStorage.setItem('user_name', values.email)
      window.location.href = '/'
    })
  }

  return (
    <div className={styles.loginBox}>
      <div className={styles.loginContentBox}>
        <h4 className={styles.loginHeader}>Feature</h4>
        <Form
          name="normal_login"
          className="login-form"
          initialValues={{ remember: true }}
          size={'large'}
          onFinish={onFinish}
        >
          <Form.Item name="email" rules={[{ required: true, message: 'Please input your Email!' }]}>
            <Input prefix={<UserOutlined className="site-form-item-icon" />} placeholder="Email" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please input your Password!' }]}
          >
            <Input
              prefix={<LockOutlined className="site-form-item-icon" />}
              type="password"
              placeholder="Password"
            />
          </Form.Item>
          <div className={styles.loginRemember}>
            <Form.Item noStyle name="remember" valuePropName="checked">
              <Checkbox>Remember me</Checkbox>
            </Form.Item>

            <a className="login-form-forgot" href="/forgot-password">
              Forgot password
            </a>
          </div>
          <Form.Item>
            <Button block type="primary" htmlType="submit" className="login-form-button">
              Login
            </Button>
          </Form.Item>
          <div className={styles.loginRemember}>
            <div className={styles.loginRemember}>
              Others
              <Button
                type="primary"
                style={{ marginLeft: 10 }}
                shape="circle"
                size="small"
                icon={<AlipayOutlined />}
              ></Button>
            </div>
            <a href="/sign-up">Sign Up</a>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default App
