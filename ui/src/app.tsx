import React, { useMemo } from 'react'

import { Layout } from 'antd'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import DataSourceDetails from '@/pages/DataSourceDetails'
import DataSources from '@/pages/DataSources'
import FeatureDetails from '@/pages/FeatureDetails'
import Features from '@/pages/Features'
import ForgotPassword from '@/pages/ForgotPassword'
import Home from '@/pages/Home'
import Jobs from '@/pages/Jobs'
import Login from '@/pages/Login'
import Management from '@/pages/Management'
import Monitoring from '@/pages/Monitoring'
import NewFeature from '@/pages/NewFeature'
import NewSource from '@/pages/NewSource'
import ProjectLineage from '@/pages/ProjectLineage'
import Projects from '@/pages/Projects'
import ResponseErrors from '@/pages/ResponseErrors'
import RoleManagement from '@/pages/RoleManagement'
import SignUp from '@/pages/SignUp'
import Users from '@/pages/Users'

import AzureMsal from './components/AzureMsal'
import Header from './components/HeaderBar/header'
import SideMenu from './components/SiderMenu/siteMenu'

const queryClient = new QueryClient()

const enableRBAC = window.environment?.enableRBAC
const authEnable: boolean = (enableRBAC ? enableRBAC : process.env.REACT_APP_ENABLE_RBAC) === 'true'

const App = () => {
  const hiderSiderPath = ['/forgot-password', '/login', '/sign-up']

  const hideSider = useMemo(() => {
    console.log('window.location.pathname', window.location.pathname)
    return !hiderSiderPath.includes(window.location.pathname)
  }, [window.location.pathname])
  return (
    <AzureMsal enable={authEnable}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Layout style={{ minHeight: '100vh', position: 'relative' }}>
            {hideSider && <SideMenu />}
            <Layout style={{ position: 'relative' }}>
              {hideSider && <Header />}
              <Layout.Content>
                <Routes>
                  <Route index element={<Home />} />
                  <Route path="/home" element={<Home />} />
                  <Route path="/users" element={<Users />} />
                  <Route path="/projects" element={<Projects />} />
                  <Route path="/dataSources" element={<DataSources />} />
                  <Route path="/features" element={<Features />} />
                  <Route path="/new-feature" element={<NewFeature />} />
                  <Route path="/new-source" element={<NewSource />} />
                  <Route
                    path="/projects/:project/features/:featureId"
                    element={<FeatureDetails />}
                  />
                  <Route
                    path="/projects/:project/dataSources/:dataSourceId"
                    element={<DataSourceDetails />}
                  />
                  <Route path="/projects/:project/lineage" element={<ProjectLineage />} />
                  <Route path="/jobs" element={<Jobs />} />
                  <Route path="/monitoring" element={<Monitoring />} />
                  <Route path="/management" element={<Management />} />
                  <Route path="/role-management" element={<RoleManagement />} />
                  <Route path="/responseErrors/:status/:detail" element={<ResponseErrors />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/forgot-password" element={<ForgotPassword />} />
                  <Route path="/sign-up" element={<SignUp />} />
                </Routes>
              </Layout.Content>
            </Layout>
          </Layout>
        </BrowserRouter>
      </QueryClientProvider>
    </AzureMsal>
  )
}

export default App
