import React, { useState, useEffect } from 'react'

import { LockOutlined, UserOutlined, AimOutlined } from '@ant-design/icons'
import { Button, message, Form, Input, Row, Col } from 'antd'
import { useNavigate } from 'react-router-dom'

import { forgotPassword } from '@/api'
import { ForgotPasswordModel } from '@/models/model'

import styles from './index.module.less'

const App: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [codeCheck, setCodeCheck] = useState<boolean>(false)
  const [code, setCode] = useState<number>(0)
  const onFinish = async () => {
    const values = (await form.validateFields()) as ForgotPasswordModel
    setCodeCheck(false)
    const response = await forgotPassword(values)
    const data = response.data
    if (data.status === 'SUCCESS') {
      message.info('Signup Success!').then(() => {
        navigate('/login')
      })
    }
  }

  const sendOpt = async () => {
    setCodeCheck(true)
    const values = await form.validateFields()
    await forgotPassword(values)
    setCode(60)
  }

  useEffect(() => {
    if (code > 0) {
      setTimeout(() => {
        setCode(code - 1)
      }, 1000)
    }
  }, [code])

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
          <Form.Item>
            <Row gutter={8}>
              <Col span={18}>
                <Form.Item
                  noStyle
                  name="captcha"
                  rules={[{ required: !codeCheck, message: 'Please input the captcha you got!' }]}
                >
                  <Input placeholder="Please Input" prefix={<AimOutlined />} />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Button block disabled={code > 0} onClick={sendOpt}>
                  Send
                </Button>
              </Col>
            </Row>
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please input your Password!' }]}
          >
            <Input prefix={<LockOutlined />} type="password" placeholder="Password" />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            rules={[{ required: true, message: 'Please input your Password!' }]}
          >
            <Input prefix={<LockOutlined />} type="password" placeholder="Confirm Password" />
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
