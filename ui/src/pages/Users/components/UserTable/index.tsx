import React, { forwardRef, useState } from 'react'

import { DeleteOutlined } from '@ant-design/icons'
import { Button, Space, notification, Popconfirm, message } from 'antd'
import { useQuery } from 'react-query'
import { useNavigate } from 'react-router-dom'

import { fetchProjects, deleteEntity, fetchUsers, removeUser } from '@/api'
import ResizeTable, { ResizeColumnType } from '@/components/ResizeTable'
import { Project, User } from '@/models/model'

import ChangeUser from '../InviteUser'

export interface ProjectTableProps {
  keyword?: string
}
const ProjectTable = (props: ProjectTableProps, ref: any) => {
  const { keyword } = props

  const [open, setOpen] = useState<boolean>(false)

  const changeUser = (userInfo: User) => {
    console.log('userInfo', userInfo)
    setOpen(true)
  }

  const columns: ResizeColumnType<User>[] = [
    {
      key: 'email',
      title: 'Email',
      dataIndex: 'email',
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
      title: 'Crete Time',
      dataIndex: 'create_time',
      resize: false
    },
    {
      key: 'Update Time',
      title: 'Update Time',
      dataIndex: 'update_time',
      resize: false
    },
    {
      key: 'action',
      title: 'Action',
      width: 240,
      resize: false,
      render: (record: User) => {
        const { name, id } = record
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
                  onDelete(id, resolve)
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
  } = useQuery<User[]>(
    ['dataSources', keyword],
    async () => {
      const params = {
        keyword
      }
      const result = await fetchUsers(params)
      return result.data
    },
    {
      retry: false,
      refetchOnWindowFocus: false
    }
  )

  const onDelete = async (entity: string, resolve: (value?: unknown) => void) => {
    try {
      await removeUser(entity)
      message.success('The user is deleted successfully.')
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
