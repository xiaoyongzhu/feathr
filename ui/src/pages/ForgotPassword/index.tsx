import React, { useState, useEffect } from 'react'

import { LockOutlined, UserOutlined, AimOutlined } from '@ant-design/icons'
import { Button, message, Form, Input, Row, Col } from 'antd'
import { useNavigate } from 'react-router-dom'

import styles from './index.module.less'

import { forgotPassword, signupOpt } from '@/api'
import { ForgotPasswordModel } from '@/models/model'

const App: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [checkLoading, setCheckLoading] = useState<boolean>(false)
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
    setCheckLoading(true)
    try {
      setCodeCheck(true)
      const values = await form.validateFields()
      const response = await signupOpt({ ...values, type: 'UPDATE_PASSWORD' })
      const data = response.data
      if (data.status === 'SUCCESS') {
        setCode(60)
      }
      setCheckLoading(false)
    } catch (e) {
      setCheckLoading(false)
    }
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
          form={form}
          name="normal_login"
          className="login-form"
          initialValues={{ remember: true }}
          size={'large'}
          onFinish={onFinish}
        >
          <Form.Item name="email" rules={[{ required: true, message: 'Please input your email!' }]}>
            <Input prefix={<UserOutlined className="site-form-item-icon" />} placeholder="Email" />
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
                <Button block disabled={code > 0} loading={checkLoading} onClick={sendOpt}>
                  Send
                </Button>
              </Col>
            </Row>
          </Form.Item>
          <Form.Item
            name="new_password"
            rules={[{ required: !codeCheck, message: 'Please input your Password!' }]}
          >
            <Input prefix={<LockOutlined />} type="password" placeholder="Password" />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            rules={[{ required: !codeCheck, message: 'Please input your Password!' }]}
          >
            <Input prefix={<LockOutlined />} type="password" placeholder="Confirm Password" />
          </Form.Item>

          <div className={styles.signUpBtnBox}>
            <Button type="primary" htmlType="submit">
              Confirm
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
