import React, { forwardRef, useState } from 'react'

import { DeleteOutlined } from '@ant-design/icons'
import { Button, Space, notification, Popconfirm, message } from 'antd'
import { useQuery } from 'react-query'
import { useNavigate } from 'react-router-dom'

import {fetchProjects, deleteEntity, fetchUsers, removeUser} from '@/api'
import ResizeTable, { ResizeColumnType } from '@/components/ResizeTable'
import { Project, User } from '@/models/model'

import ChangeUser from '../InviteUser'

export interface ProjectTableProps {
  project?: string
}
const ProjectTable = (props: ProjectTableProps, ref: any) => {
  const temp_organization_id = 'a1ccf112-3367-4c13-8c38-b4a8555497c2'
  const { project } = props

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
    ['Projects', project],
    async () => {
      // todo: keyword, and need parse result, content in the data
      const result = await fetchUsers(temp_organization_id, '')
      return []
      // return result.reduce((list, item: string) => {
      //   const text = project?.trim().toLocaleLowerCase()
      //   if (!text || item.includes(text)) {
      //     list.push({
      //       name: item,
      //       id: '',
      //       email: '',
      //       phone: '',
      //       createTime: ''
      //     })
      //   }
      //   return list
      // }, [] as User[])
    },
    {
      retry: false,
      refetchOnWindowFocus: false
    }
  )

  const onDelete = async (entity: string, resolve: (value?: unknown) => void) => {
    try {
      await removeUser(temp_organization_id, entity)
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
