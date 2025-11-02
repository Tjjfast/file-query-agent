'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import ChatInput from './ChatInput'
import MessageArea from './MessageArea'
import FileUpload from './FileUpload/FileUpload'

const ChatArea = () => {
  const [showUpload, setShowUpload] = useState(false)

  return (
    <main className="relative m-1.5 flex flex-grow flex-col rounded-xl bg-background">
      <MessageArea />
      <div className="sticky bottom-0 ml-9 px-4 pb-2 bg-background">
        {showUpload && <FileUpload />}
        <div className="flex items-center justify-between mb-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowUpload(!showUpload)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            {showUpload ? 'Hide Upload' : 'Upload Knowledge'}
          </Button>
        </div>
        <ChatInput />
      </div>
    </main>
  )
}

export default ChatArea
