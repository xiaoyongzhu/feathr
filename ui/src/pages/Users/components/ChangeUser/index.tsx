import React, { forwardRef, useEffect, useRef } from 'react'

import { Form, Modal, Input, Select, message } from 'antd'

import { changeUser } from '@/api'

const { Option } = Select

export interface ChangeUserProps {
  open: boolean
  setOpen: any
  userInfo?: { role: string; id: string }
  resetList?: () => void
}

const { Item } = Form

const ChangeUser = (props: ChangeUserProps, ref: any) => {
  const [form] = Form.useForm()

  const { open, setOpen, userInfo, resetList } = props

  const hideModal = () => {
    setOpen(false)
  }

  const onFinish = async () => {
    const params = await form.getFieldsValue()
    const { status } = await changeUser(params, userInfo?.id || '')
    if (status === 'SUCCESS') {
      setOpen(false)
      message.success('Success')
      if (resetList) {
        resetList()
      }
    }
  }

  useEffect(() => {
    if (open && userInfo && userInfo.role) {
      form.setFieldsValue({ role: userInfo.role })
    }
  }, [open, userInfo])

  return (
    <Modal
      title="Change User"
      open={open}
      okText="Confirm"
      cancelText="Cancel"
      onOk={onFinish}
      onCancel={hideModal}
    >
      <Form form={form} name="control-hooks" labelCol={{ span: '5' }} onFinish={onFinish}>
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

const SearchBarComponent = forwardRef<unknown, ChangeUserProps>(ChangeUser)

SearchBarComponent.displayName = 'SearchBarComponent'

export default SearchBarComponent
