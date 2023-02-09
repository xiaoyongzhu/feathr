import React, { forwardRef, useRef } from 'react'

import { Form, Modal, Input, Select } from 'antd'

const { Option } = Select

export interface InviteUserProps {
  open: boolean
  setOpen: any
}

const { Item } = Form

const InviteUser = (props: InviteUserProps, ref: any) => {
  const [form] = Form.useForm()

  const { open, setOpen } = props

  const hideModal = () => {
    setOpen(false)
  }

  const onFinish = () => {
    console.log('onFinish')
    setOpen(false)
  }

  return (
    <Modal
      title="Invite User"
      open={open}
      okText="Confirm"
      cancelText="Cancel"
      onOk={onFinish}
      onCancel={hideModal}
    >
      <Form form={form} name="control-hooks" labelCol={{ span: '5' }} onFinish={onFinish}>
        <Item name="email" label="Email" rules={[{ required: true }]}>
          <Input placeholder="Please Input Email" />
        </Item>
        <Item name="role" label="Role" rules={[{ required: true }]}>
          <Select allowClear placeholder="Select Role">
            <Option value="admin">Admin</Option>
            <Option value="user">User</Option>
            <Option value="other">Other</Option>
          </Select>
        </Item>
      </Form>
    </Modal>
  )
}

const SearchBarComponent = forwardRef<unknown, InviteUserProps>(InviteUser)

SearchBarComponent.displayName = 'SearchBarComponent'

export default SearchBarComponent
