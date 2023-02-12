import React, { useState } from 'react'

import { PageHeader } from 'antd'

import SearchBar from './components/SearchBar'
import ProjectTable from './components/UserTable'

const Projects = () => {
  const [keyword, setKeyword] = useState<string>('')

  const onSearch = ({ keyword }: { keyword: string }) => {
    setKeyword(keyword)
  }

  return (
    <div className="page">
      <PageHeader title="Users" ghost={false}>
        <SearchBar onSearch={onSearch} />
        <ProjectTable keyword={keyword} />
      </PageHeader>
    </div>
  )
}

export default Projects
