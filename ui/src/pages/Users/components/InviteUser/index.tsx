import React, { forwardRef, useState } from 'react'

import { Form, Modal, Input, Select, message } from 'antd'

import { inviteUser } from '@/api'

const { Option } = Select

export interface InviteUserProps {
  open: boolean
  setOpen: any
  resetList?: () => void
}

const { Item } = Form

const InviteUser = (props: InviteUserProps, ref: any) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState<boolean>(false)
  const { open, setOpen, resetList } = props

  const hideModal = () => {
    setOpen(false)
  }

  const onFinish = async () => {
    setLoading(true)
    const params = await form.getFieldsValue()
    const { status } = await inviteUser(params)
    if (status === 'SUCCESS') {
      setOpen(false)
      message.success('Success')
      if (resetList) {
        resetList()
      }
    }
    setLoading(false)
  }

  return (
    <Modal
      title="Invite User"
      open={open}
      okText="Confirm"
      cancelText="Cancel"
      confirmLoading={loading}
      onOk={onFinish}
      onCancel={hideModal}
    >
      <Form form={form} name="control-hooks" labelCol={{ span: '5' }} onFinish={onFinish}>
        <Item name="email" label="Email" rules={[{ required: true }]}>
          <Input placeholder="Please Input Email" />
        </Item>
        <Item name="role" label="Role" rules={[{ required: true }]}>
          <Select allowClear placeholder="Select Role">
            <Option value="ADMIN">Admin</Option>
            <Option value="USER">User</Option>
          </Select>
        </Item>
      </Form>
    </Modal>
  )
}

const SearchBarComponent = forwardRef<unknown, InviteUserProps>(InviteUser)

SearchBarComponent.displayName = 'SearchBarComponent'

export default SearchBarComponent
