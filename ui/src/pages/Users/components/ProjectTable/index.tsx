import React, { forwardRef, useState } from 'react'

import { DeleteOutlined } from '@ant-design/icons'
import { Button, Space, notification, Popconfirm, message } from 'antd'
import { useQuery } from 'react-query'
import { useNavigate } from 'react-router-dom'

import { fetchProjects, deleteEntity } from '@/api'
import ResizeTable, { ResizeColumnType } from '@/components/ResizeTable'
import { Project } from '@/models/model'

import ChangeUser from '../InviteUser'

export interface ProjectTableProps {
  project?: string
}
const ProjectTable = (props: ProjectTableProps, ref: any) => {
  const { project } = props

  const [open, setOpen] = useState<boolean>(false)

  const changeUser = (userInfo: Project) => {
    console.log('userInfo', userInfo)
    setOpen(true)
  }

  const columns: ResizeColumnType<Project>[] = [
    {
      key: 'email',
      title: 'Email',
      dataIndex: 'email',
      resize: false
    },
    {
      key: 'phone',
      title: 'Phone',
      dataIndex: 'phone',
      resize: false
    },
    {
      key: 'role',
      title: 'Role',
      dataIndex: 'role',
      resize: false
    },
    {
      key: 'Crete Time',
      title: 'Email',
      dataIndex: 'email',
      resize: false
    },
    {
      key: 'Update Time',
      title: 'Email',
      dataIndex: 'email',
      resize: false
    },
    {
      key: 'action',
      title: 'Action',
      width: 240,
      resize: false,
      render: (record: Project) => {
        const { name } = record
        return (
          <Space size="middle">
            <Button
              ghost
              type="primary"
              onClick={() => {
                changeUser(record)
              }}
            >
              Change
            </Button>
            <Popconfirm
              title="Are you sure to delete this user?"
              placement="topRight"
              onConfirm={() => {
                return new Promise((resolve) => {
                  onDelete(name, resolve)
                })
              }}
            >
              <Button danger ghost type="primary" icon={<DeleteOutlined />}>
                Detete
              </Button>
            </Popconfirm>
          </Space>
        )
      }
    }
  ]

  const {
    isLoading,
    data: tableData,
    refetch
  } = useQuery<Project[]>(
    ['Projects', project],
    async () => {
      const reuslt = await fetchProjects()

      return reuslt.reduce((list, item: string) => {
        const text = project?.trim().toLocaleLowerCase()
        if (!text || item.includes(text)) {
          list.push({ name: item })
        }
        return list
      }, [] as Project[])
    },
    {
      retry: false,
      refetchOnWindowFocus: false
    }
  )

  const onDelete = async (entity: string, resolve: (value?: unknown) => void) => {
    try {
      await deleteEntity(entity)
      message.success('The project is deleted successfully.')
      refetch()
    } catch (e: any) {
      notification.error({
        message: '',
        description: e.detail,
        placement: 'top'
      })
    } finally {
      resolve()
    }
  }

  return (
    <>
      <ResizeTable
        rowKey="name"
        loading={isLoading}
        columns={columns}
        dataSource={tableData}
        scroll={{ x: '100%' }}
      />
      <ChangeUser open={open} setOpen={setOpen}></ChangeUser>
    </>
  )
}

const ProjectTableComponent = forwardRef<unknown, ProjectTableProps>(ProjectTable)

ProjectTableComponent.displayName = 'ProjectTableComponent'

export default ProjectTableComponent
