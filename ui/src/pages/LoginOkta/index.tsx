import React from 'react'

import { message } from 'antd'
import Cookies from 'js-cookie'

import { loginOkta } from '@/api'
import { LoginOktaModel } from '@/models/model'

const App: React.FC = () => {
  const handleLoginOkta = (code: string, redirect: string) => {
    loginOkta({ code: code, redirect_uri: redirect }).then((response) => {
      let data = response.data
      if (data.status === 'SUCCESS') {
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
        localStorage.setItem('organization_id', data.organizations[0].organization_id)
        localStorage.setItem('user_name', data.name)
        window.location.href = '/'
      }
    })
  }

  // 在组件挂载时进行重定向
  React.useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search)
    const code = queryParams.get('code')
    if (!code) {
      throw Error('Code cannot be null')
    }
    const state = queryParams.get('state')
    if (!state) {
      throw Error('State cannot be null')
    }
    if (state !== 'feathr') {
      throw Error('Incorrect State')
    }
    const oktaCallbackUri = process.env.REACT_APP_OKTA_CALLBACK_URI
    if (!oktaCallbackUri) {
      throw Error('REACT_APP_OKTA_CALLBACK_URI cannot be none')
    }
    handleLoginOkta(code, oktaCallbackUri)
  }, [])

  return <div>Logging in...</div>
}

export default App
