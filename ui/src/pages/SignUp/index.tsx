import React from 'react'

import { LockOutlined, UserOutlined, AimOutlined } from '@ant-design/icons'
import {Button, Form, Input, Row, Col, message} from 'antd'

import { useNavigate } from 'react-router-dom'
import styles from './index.module.less'
import {signup} from '@/api'
import {SignupModel} from '@/models/model'

const App: React.FC = () => {
  const navigate = useNavigate()
  const onFinish = (values: SignupModel) => {
    console.log('Received values of form: ', values)
    signup(values).then(response=>{
      let data = response.data
      if (data.status !== 'SUCCESS') {
        message.warning(response.data.message).then()
        return
      }
      message.info('Signup Success!').then(()=>{
        navigate(`/login`)
      })
    }).catch (error =>{
      message.warning(error.message).then()
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
          <Form.Item
            name="email"
            rules={[{ required: true, message: 'Please input your Email!' }]}
          >
            <Input
              prefix={<UserOutlined className="site-form-item-icon" />}
              placeholder="email"
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
