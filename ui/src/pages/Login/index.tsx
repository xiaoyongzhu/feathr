import React from 'react'

import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { Button, Checkbox, Form, Input, message } from 'antd'
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
      if (data.status === 'SUCCESS') {
        data = data.data
        if (data.organizations.length === 0) {
          // todo: This user does not have any organizations, need redirect no organization page!
          message.success('No organizations exist. Please join an organization before logging in.')
          return
        }
        message.success('Login Success')
        const token = data.token
        Cookies.set('token', token, {
          expires: 7
        })
        localStorage.setItem('organization_id', data.organizations[0].organization_id)
        localStorage.setItem('user_name', values.email)
        window.location.href = '/'
      }
    })
  }

  const handleOktaLogin = () => {
    const oktaAuthorizeUrl = process.env.REACT_APP_OKTA_AUTHORIZE_URL
    if (!oktaAuthorizeUrl) {
      throw Error('REACT_APP_OKTA_AUTHORIZE_URL cannot be none')
    }

    const oktaClientId = process.env.REACT_APP_OKTA_CLIENT_ID
    if (!oktaClientId) {
      throw Error('REACT_APP_OKTA_CLIENT_ID cannot be none')
    }

    const oktaCallbackUri = process.env.REACT_APP_OKTA_CALLBACK_URI
    if (!oktaCallbackUri) {
      throw Error('REACT_APP_OKTA_CALLBACK_URI cannot be none')
    }
    let authAuthorizeUrl = oktaAuthorizeUrl
    authAuthorizeUrl += '?response_type=code'
    authAuthorizeUrl += '&client_id=' + oktaClientId
    authAuthorizeUrl += '&redirect_uri=' + encodeURIComponent(oktaCallbackUri)
    authAuthorizeUrl += '&scope=openid+profile+email&state=feathr'
    window.location.href = authAuthorizeUrl
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
            <div className={styles.loginRememberOther}>
              Others
              <div onClick={handleOktaLogin}>
                <img
                  style={{ marginLeft: 10, width: '35px', cursor: 'pointer' }}
                  src={'/okta-icon.jpg'}
                  alt="Okta"
                />
              </div>
            </div>
            <a href="/sign-up">Sign Up</a>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default App
