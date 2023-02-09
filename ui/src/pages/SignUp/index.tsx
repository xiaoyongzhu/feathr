import React from 'react'

import { LockOutlined, UserOutlined, AimOutlined } from '@ant-design/icons'
import { Button, Form, Input, Row, Col } from 'antd'

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
          <Form.Item>
            <Row gutter={8}>
              <Col span={18}>
                <Form.Item
                  noStyle
                  name="captcha"
                  rules={[{ required: true, message: 'Please input the captcha you got!' }]}
                >
                  <Input placeholder="Please Input" prefix={<AimOutlined />} />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Button block>Send</Button>
              </Col>
            </Row>
          </Form.Item>
          <div className={styles.signUpBtnBox}>
            <Button type="primary" htmlType="submit">
              Sign Up
            </Button>
            <a className="login-form-forgot" href="/login">
              Login
            </a>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default App
