import React, { useState } from 'react'

import { PageHeader } from 'antd'

import ProjectTable from './components/UserTable'
import SearchBar from './components/SearchBar'

const Projects = () => {
  const [project, setProject] = useState<string>('')

  const onSearch = ({ project }: { project: string }) => {
    setProject(project)
  }

  return (
    <div className="page">
      <PageHeader title="Users" ghost={false}>
        <SearchBar onSearch={onSearch} />
        <ProjectTable project={project} />
      </PageHeader>
    </div>
  )
}

export default Projects
