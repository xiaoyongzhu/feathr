import React from 'react'

import { LockOutlined, UserOutlined, AlipayOutlined } from '@ant-design/icons'
import { Button, Checkbox, Form, Input, Row, Col } from 'antd'

import styles from './index.module.less'

const App: React.FC = () => {
  const onFinish = (values: any) => {
    console.log('Received values of form: ', values)
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
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please input your Username!' }]}
          >
            <Input
              prefix={<UserOutlined className="site-form-item-icon" />}
              placeholder="Username"
            />
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
            <Button
              block
              type="primary"
              htmlType="submit"
              className="login-form-button"
              onClick={() => {
                window.location.href = '/'
              }}
            >
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
