import React, { useEffect, useState } from 'react'

import { LockOutlined, UserOutlined, AimOutlined } from '@ant-design/icons'
import { Button, Form, Input, Row, Col, message } from 'antd'
import { useNavigate } from 'react-router-dom'

import { signup, signupOpt } from '@/api'
import { SignupModel } from '@/models/model'

import styles from './index.module.less'

const App: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState<boolean>(false)
  const [codeCheck, setCodeCheck] = useState<boolean>(false)
  const [checkLoading, setCheckLoading] = useState<boolean>(false)

  const [code, setCode] = useState<number>(0)
  const onFinish = async () => {
    setLoading(true)
    const values = (await form.validateFields()) as SignupModel
    setCodeCheck(false)
    const response = await signup(values)
    const data = response.data
    if (data.status === 'SUCCESS') {
      message.info('Signup Success!').then(() => {
        navigate('/login')
      })
    }
    setLoading(false)
  }

  const sendOpt = async () => {
    setCheckLoading(true)
    try {
      setCodeCheck(true)
      const values = await form.validateFields()
      const response = await signupOpt({ ...values, type: 'REGISTER' })
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
          name="normal_login"
          className="login-form"
          form={form}
          initialValues={{ remember: true }}
          size={'large'}
          onFinish={onFinish}
        >
          <Form.Item name="email" rules={[{ required: true, message: 'Please input your Email!' }]}>
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
                  {code > 0 ? code : 'Send'}
                </Button>
              </Col>
            </Row>
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: !codeCheck, message: 'Please input your Password!' }]}
          >
            <Input
              prefix={<LockOutlined className="site-form-item-icon" />}
              type="password"
              placeholder="Password"
            />
          </Form.Item>

          <div className={styles.signUpBtnBox}>
            <Button type="primary" htmlType="submit" loading={loading}>
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
