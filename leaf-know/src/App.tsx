import "./App.css";
import { useEffect, useState } from "react"
// import { create } from "zustand"
import { load } from '@tauri-apps/plugin-store'
import { appDataDir, join } from '@tauri-apps/api/path'
// import { listen } from '@tauri-apps/api/event'
import { useAppStore } from "./main"
import { Toaster } from "@/components/ui/sonner"
import { SidebarProvider } from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { AppSidebar } from "./app-sidebar"
import { AppWorkspace } from "./app-workspace"
import Splash from "./splash"
import { useBridgeEvents } from "@/hooks/useBridgeEvents"
import { ChatSession, createSmartSession, pinFile, updateSession, deleteSession } from "./lib/chat-session-api"

const API_BASE_URL = 'http://127.0.0.1:60000'



// ==================== 工具函数 ====================

// 保存最近使用的会话ID到Tauri Store
async function saveLastUsedSession(sessionId: number): Promise<void> {
  try {
    const appDataPath = await appDataDir()
    const storePath = await join(appDataPath, 'settings.json')
    const store = await load(storePath, { defaults: {  }, autoSave: false });
    
    await store.set('lastUsedSessionId', sessionId)
    await store.save()
    console.log('Last used session saved to settings.json:', sessionId)
  } catch (error) {
    console.error('Failed to save last used session:', error)
  }
}

// 从Tauri Store读取最近使用的会话ID
async function getLastUsedSession(): Promise<number | null> {
  try {
    const appDataPath = await appDataDir()
    const storePath = await join(appDataPath, 'settings.json')
    const store = await load(storePath, { defaults: {  }, autoSave: false });
    
    const sessionId = await store.get('lastUsedSessionId') as number | null
    console.log('Last used session loaded from settings.json:', sessionId)
    return sessionId
  } catch (error) {
    console.error('Failed to load last used session:', error)
    return null
  }
}

function App() {
  const {
    isApiReady,
    setApiReady,
  } = useAppStore()

  const [showSplash, setShowSplash] = useState(true)

  // Dialog 状态管理
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedSession, setSelectedSession] = useState<{id: number, name: string} | null>(null)
  const [newSessionName, setNewSessionName] = useState("")
  
  // 处理重命名对话框关闭，确保状态完全重置并清理DOM
  const handleRenameDialogClose = (open: boolean) => {
    if (!open) {
      setRenameDialogOpen(false)
      // 立即清理状态
      setSelectedSession(null)
      setNewSessionName("")
      
      // 强制恢复 body 的交互能力 - 多次尝试确保生效
      const cleanup = () => {
        // 恢复 pointer-events
        document.body.style.pointerEvents = ''
        document.documentElement.style.pointerEvents = ''
        document.body.style.cursor = ''
        
        // 移除所有可能的遮罩层和 Portal 内容
        const overlays = document.querySelectorAll('[data-radix-dialog-overlay]')
        overlays.forEach(overlay => overlay.remove())
        
        const portals = document.querySelectorAll('[data-radix-portal]')
        portals.forEach(portal => {
          const dialogContent = portal.querySelector('[data-radix-dialog-content]')
          if (!dialogContent || dialogContent.getAttribute('data-state') === 'closed') {
            portal.remove()
          }
        })
        
        // 移除 Radix 添加的属性
        document.body.removeAttribute('data-scroll-locked')
        document.body.removeAttribute('inert')
        document.body.style.overflow = ''
        document.body.style.paddingRight = ''
        document.body.style.touchAction = ''
        
        // 移除所有可能阻止交互的 CSS
        const allElements = document.querySelectorAll('*')
        allElements.forEach(el => {
          const computedStyle = getComputedStyle(el)
          if (computedStyle.pointerEvents === 'none' && 
              computedStyle.position === 'fixed' && 
              parseInt(computedStyle.zIndex) > 40) {
            (el as HTMLElement).style.pointerEvents = ''
          }
        })
        
        console.log('Rename dialog closed, restored pointer events')
      }
      
      // 立即执行一次
      setTimeout(cleanup, 0)
      // 再执行一次确保生效
      setTimeout(cleanup, 100)
      // 最后再执行一次
      setTimeout(cleanup, 300)
    } else {
      setRenameDialogOpen(true)
    }
  }
  
  // 处理删除对话框关闭，确保状态完全重置并清理DOM
  const handleDeleteDialogClose = (open: boolean) => {
    if (!open) {
      setDeleteDialogOpen(false)
      // 立即清理状态
      setSelectedSession(null)
      
      // 强制恢复 body 的交互能力
      setTimeout(() => {
        document.body.style.pointerEvents = ''
        document.documentElement.style.pointerEvents = ''
        
        // 移除所有可能的遮罩层
        const overlays = document.querySelectorAll('[data-radix-dialog-overlay]')
        overlays.forEach(overlay => overlay.remove())
        
        // 移除 Radix 添加的 inert 属性和样式
        document.body.removeAttribute('data-scroll-locked')
        document.body.style.overflow = ''
        document.body.style.paddingRight = ''
        
        console.log('Delete dialog closed, restored pointer events')
      }, 100)
    } else {
      setDeleteDialogOpen(true)
    }
  }

  // 会话状态管理
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null)
  
  // 新生成会话状态（用于控制标题动画）
  const [newlyGeneratedSessionId, setNewlyGeneratedSessionId] = useState<number | null>(null)
  
  // 临时Pin文件状态（在会话创建前临时保存）
  const [tempPinnedFiles, setTempPinnedFiles] = useState<Array<{
    file_path: string
    file_name: string
    metadata?: Record<string, any>
  }>>([])
  
  // 临时选择的工具状态（在会话创建前临时保存）
  const [tempSelectedTools, setTempSelectedTools] = useState<string[]>([])
  
  // 聊天重置触发器
  const [chatResetTrigger, setChatResetTrigger] = useState(0)
  
  // Sidebar刷新触发器
  const [sidebarRefreshTrigger, setSidebarRefreshTrigger] = useState(0)
  
  // 搜索对话框状态
  const [searchOpen, setSearchOpen] = useState(false)
  
  // 全局清理遗留的 Dialog overlay 和恢复 pointer-events（防御性措施）
  useEffect(() => {
    const cleanupDialogArtifacts = () => {
      // 如果没有打开的 Dialog，强制恢复交互能力
      if (!renameDialogOpen && !deleteDialogOpen && !searchOpen) {
        // 恢复 pointer-events
        if (document.body.style.pointerEvents === 'none' || 
            document.documentElement.style.pointerEvents === 'none') {
          console.warn('Detected blocked pointer events, forcing restore')
          document.body.style.pointerEvents = ''
          document.documentElement.style.pointerEvents = ''
        }
        
        // 清理遗留的 overlay
        const overlays = document.querySelectorAll('[data-radix-dialog-overlay]')
        if (overlays.length > 0) {
          console.warn('Detected orphaned overlays:', overlays.length)
          overlays.forEach(overlay => overlay.remove())
        }
        
        // 清理 Radix 的滚动锁定
        if (document.body.hasAttribute('data-scroll-locked')) {
          document.body.removeAttribute('data-scroll-locked')
          document.body.style.overflow = ''
          document.body.style.paddingRight = ''
        }
      }
    }
    
    // 定期检查（每500毫秒）
    const intervalId = setInterval(cleanupDialogArtifacts, 500)
    
    return () => {
      clearInterval(intervalId)
      cleanupDialogArtifacts() // 组件卸载时最后清理一次
    }
  }, [renameDialogOpen, deleteDialogOpen, searchOpen])

  // 恢复最近使用的会话
  const restoreLastUsedSession = async () => {
    if (!isApiReady) return
    
    try {
      const lastSessionId = await getLastUsedSession()
      if (lastSessionId) {
        // 尝试从API获取会话信息
        const { getSessions } = await import('./lib/chat-session-api')
        const result = await getSessions(1, 50) // 获取会话列表
        const session = result.sessions.find(s => s.id === lastSessionId)
        
        if (session) {
          setCurrentSession(session)
          setCurrentSessionId(session.id)
        } else {
          console.log('Last used session not found:', lastSessionId)
        }
      }
    } catch (error) {
      console.error('Failed to restore last used session:', error)
    }
  }

  // API就绪后恢复最近会话
  useEffect(() => {
    if (isApiReady) {
      restoreLastUsedSession()
      
      // 清理函数
      return () => {
       
      }
    }
  }, [isApiReady])

  // 会话处理函数
  const handleSessionSwitch = async (session: ChatSession | null) => {
    try {
      if (!session) {
        // 如果session为null，清空当前会话
        setCurrentSession(null)
        setCurrentSessionId(null)
        return
      }
      
      setCurrentSession(session)
      setCurrentSessionId(session.id)
      
      // 清空临时Pin文件（切换到已存在的会话）
      setTempPinnedFiles([])
      
      // 清空临时工具选择（切换到已存在的会话）
      setTempSelectedTools([])
      
      
      
      // 保存到Tauri Store
      await saveLastUsedSession(session.id)
      
      console.log('Switched to session:', session.name, session.id)
    } catch (error) {
      console.error('Failed to switch session:', error)
    }
  }

  // 创建新会话的处理（仅设置为准备状态，实际创建延迟到第一条消息）
  const handleCreateSession = async () => {
    try {
      // 清空当前会话状态，准备新会话
      setCurrentSession(null)
      setCurrentSessionId(null)
      
      // 触发聊天组件重置
      setChatResetTrigger(prev => prev + 1)
    } catch (error) {
      console.error('Failed to prepare new session:', error)
    }
  }

  // 重命名会话处理函数
  const handleRenameSession = async (sessionId: number, newName: string): Promise<void> => {
    try {
      await updateSession(sessionId, newName)
      
      // 如果重命名的是当前会话，更新当前会话状态
      if (currentSession && currentSession.id === sessionId) {
        setCurrentSession({ ...currentSession, name: newName })
      }
      
      // 触发侧边栏刷新
      setSidebarRefreshTrigger(prev => prev + 1)
      
      console.log('Session renamed successfully:', newName)
    } catch (error) {
      console.error('Failed to rename session:', error)
      throw error
    }
  }

  // 删除会话处理函数
  const handleDeleteSession = async (sessionId: number): Promise<void> => {
    try {
      await deleteSession(sessionId)
      
      // 如果删除的是当前会话，清空当前会话状态
      if (currentSession && currentSession.id === sessionId) {
        setCurrentSession(null)
        setCurrentSessionId(null)
      }
      
      // 触发侧边栏刷新
      setSidebarRefreshTrigger(prev => prev + 1)
      
      console.log('Session deleted successfully')
    } catch (error) {
      console.error('Failed to delete session:', error)
      throw error
    }
  }
  
  // 处理会话更新（例如进入/退出共读模式）
  const handleSessionUpdate = (updatedSession: ChatSession) => {
    setCurrentSession(updatedSession)
    // 会话ID不变，无需更新currentSessionId
    console.log('会话已更新:', updatedSession)
  }

  // 实际创建会话（在用户发送第一条消息时调用）
  const createSessionFromMessage = async (firstMessageContent: string): Promise<ChatSession> => {
    try {
      // 使用LLM生成智能会话名称
      const newSession = await createSmartSession(firstMessageContent)
      
      // 设置为当前会话
      setCurrentSession(newSession)
      setCurrentSessionId(newSession.id)
      
      // 标记为新生成的会话，用于sidebar的打字机效果
      setNewlyGeneratedSessionId(newSession.id)
      
      // 将临时Pin文件绑定到新会话
      if (tempPinnedFiles.length > 0) {
        for (const file of tempPinnedFiles) {
          try {
            await pinFile(newSession.id, file.file_path, file.file_name, file.metadata)
          } catch (error) {
            console.error('Failed to bind temp pinned file to new session:', error)
          }
        }
        // 清空临时Pin文件
        setTempPinnedFiles([])
        
        // 清空临时工具选择（已经在AiSdkChat中处理了工具应用）
        setTempSelectedTools([])
      }
      
      // 保存到Tauri Store
      await saveLastUsedSession(newSession.id)
      
      // 触发sidebar刷新列表
      setSidebarRefreshTrigger(prev => prev + 1)
      
      console.log('Created new session:', newSession.name, newSession.id)
      return newSession
    } catch (error) {
      console.error('Failed to create session from message:', error)
      throw error
    }
  }

  // 添加临时工具选择
  const addTempSelectedTool = (toolName: string) => {
    setTempSelectedTools(prev => {
      if (!prev.includes(toolName)) {
        return [...prev, toolName]
      }
      return prev
    })
  }

  // 移除临时工具选择
  const removeTempSelectedTool = (toolName: string) => {
    setTempSelectedTools(prev => prev.filter(tool => tool !== toolName))
  }

  // 处理会话标题动画完成
  const handleTitleAnimationComplete = (sessionId: number) => {
    if (newlyGeneratedSessionId === sessionId) {
      setNewlyGeneratedSessionId(null)
    }
  }

  // 确认重命名处理
  const confirmRename = async () => {
    if (selectedSession && newSessionName.trim() && newSessionName !== selectedSession.name) {
      try {
        await updateSession(selectedSession.id, newSessionName.trim())
        
        // 如果重命名的是当前会话，更新当前会话状态
        if (currentSession && currentSession.id === selectedSession.id) {
          setCurrentSession({ ...currentSession, name: newSessionName.trim() })
        }
        
        // 触发侧边栏刷新
        setSidebarRefreshTrigger(prev => prev + 1)
        
        console.log('Session renamed successfully:', newSessionName)
      } catch (error) {
        console.error('Failed to rename session:', error)
      }
    }
    handleRenameDialogClose(false)
  }

  // 确认删除处理
  const confirmDelete = async () => {
    if (selectedSession) {
      try {
        await deleteSession(selectedSession.id)
        
        // 如果删除的是当前会话，清空当前会话状态
        if (currentSession && currentSession.id === selectedSession.id) {
          setCurrentSession(null)
          setCurrentSessionId(null)
        }
        
        // 触发侧边栏刷新
        setSidebarRefreshTrigger(prev => prev + 1)
        
        console.log('Session deleted successfully')
      } catch (error) {
        console.error('Failed to delete session:', error)
      }
    }
    handleDeleteDialogClose(false)
  }


  // * 监听来自Rust的IPC事件
  useBridgeEvents(
    {
      'api-ready': (payload: any) => {
        console.log("App.tsx: Received 'api-ready' event from backend.", payload)
        setApiReady(true) // Update global state so all components can react
      },
      
    },
    { showToasts: false, logEvents: true }
  )

  useEffect(() => {
    const startupSequence = async () => {
      // 健康检查在这里只作为后备方案，不会与全局状态冲突
      // 仅在始终没收到'api-ready'事件时才进行检查
        console.log("App.tsx: Performing backup health check...")
      
      const max_retries = 10000
      const retry_interval = 1000
      
      if (!isApiReady) {
        for (let attempt = 1; attempt <= max_retries; attempt++) {
          try {
            const response = await fetch(`${API_BASE_URL}/health`, {
              method: "GET",
              signal: AbortSignal.timeout(2000),
            })
            
            if (response.ok) {
              console.log(`App.tsx: API is ready (attempt ${attempt}/${max_retries})`)
              setApiReady(true)
              break
            }
            
            // 响应不是 ok，但连接成功了（静默处理）
          } catch (error) {
            // 静默处理连接错误，不输出到控制台（这是预期的）
            
            // 只在最后一次尝试时输出警告
            if (attempt === max_retries) {
              console.warn(`App.tsx: API health check failed after ${max_retries} attempts`)
              setApiReady(false)
            }
          }
          
          // 如果还有重试次数，等待后继续
          if (attempt < max_retries) {
            await new Promise((resolve) => setTimeout(resolve, retry_interval))
          }
        }
      }
    }
    
    startupSequence()
  }, [])

  if (showSplash){
    return (
      <Splash setShowSplash={setShowSplash} />
    )
  }
  return (
      <div className="w-full h-screen m-0 p-0 flex flex-row justify-center text-center overflow-hidden">
        {/* <div className="flex-1 h-full bg-amber-200">
        </div>
        <div className="flex-1 h-full bg-green-200"></div> */}
        <SidebarProvider>
          <AppSidebar 
            currentSessionId={currentSessionId ?? undefined}
            onSessionSwitch={handleSessionSwitch}
            onCreateSession={handleCreateSession}
            refreshTrigger={sidebarRefreshTrigger}
            newlyGeneratedSessionId={newlyGeneratedSessionId}
            onTitleAnimationComplete={handleTitleAnimationComplete}
            onRenameSession={handleRenameSession}
            onDeleteSession={handleDeleteSession}
            searchOpen={searchOpen}
            onSearchOpenChange={setSearchOpen}
            renameDialogOpen={renameDialogOpen}
            onRenameDialogOpenChange={handleRenameDialogClose}
            deleteDialogOpen={deleteDialogOpen}
            onDeleteDialogOpenChange={handleDeleteDialogClose}
            selectedSession={selectedSession}
            onSelectedSessionChange={setSelectedSession}
            newSessionName={newSessionName}
            onNewSessionNameChange={setNewSessionName}
            onConfirmRename={confirmRename}
            onConfirmDelete={confirmDelete}
          />
          <AppWorkspace 
            currentSession={currentSession}
            currentSessionId={currentSessionId}
            // tempPinnedFiles={tempPinnedFiles}
            tempSelectedTools={tempSelectedTools}
            onCreateSessionFromMessage={createSessionFromMessage}
            // onAddTempPinnedFile={addTempPinnedFile}
            // onRemoveTempPinnedFile={removeTempPinnedFile}
            onAddTempSelectedTool={addTempSelectedTool}
            onRemoveTempSelectedTool={removeTempSelectedTool}
            chatResetTrigger={chatResetTrigger}
            onSessionUpdate={handleSessionUpdate}
          />
        </SidebarProvider>


      {/* 重命名会话Dialog - 移到最外层，避免与Sidebar层级冲突 */}
      {renameDialogOpen && (
        <Dialog 
          key={`rename-dialog-${selectedSession?.id || 'new'}`}
          open={renameDialogOpen} 
          onOpenChange={handleRenameDialogClose}
        >
          <DialogContent 
            className="max-w-md z-100" 
            onEscapeKeyDown={(e) => {
              e.preventDefault()
              handleRenameDialogClose(false)
            }}
            onInteractOutside={() => {
              // 允许点击外部关闭
              handleRenameDialogClose(false)
            }}
            onPointerDownOutside={() => {
              // 允许点击外部关闭
              handleRenameDialogClose(false)
            }}
          >
            <DialogHeader>
              <DialogTitle>{"重命名会话"}</DialogTitle>
              <DialogDescription>
                {"请输入新的会话名称"}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <Input
                value={newSessionName}
                onChange={(e) => setNewSessionName(e.target.value)}
                placeholder={"会话名称"}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    confirmRename()
                  }
                }}
                autoFocus
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => handleRenameDialogClose(false)}>
                {"取消"}
              </Button>
              <Button onClick={confirmRename} disabled={!newSessionName.trim()}>
                {"确认"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* 删除会话确认Dialog - 移到最外层，避免与Sidebar层级冲突 */}
      {deleteDialogOpen && (
        <Dialog 
          key={`delete-dialog-${selectedSession?.id || 'new'}`}
          open={deleteDialogOpen} 
          onOpenChange={handleDeleteDialogClose}
        >
          <DialogContent 
            className="max-w-md z-100"
            onEscapeKeyDown={(e) => {
              e.preventDefault()
              handleDeleteDialogClose(false)
            }}
            onInteractOutside={() => {
              // 允许点击外部关闭
              handleDeleteDialogClose(false)
            }}
            onPointerDownOutside={() => {
              // 允许点击外部关闭
              handleDeleteDialogClose(false)
            }}
          >
            <DialogHeader>
              <DialogTitle>{"删除会话"}</DialogTitle>
              <DialogDescription>
                {`确定要删除会话 "${selectedSession?.name}" 吗？`}
              </DialogDescription>
            </DialogHeader>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => handleDeleteDialogClose(false)}>
                {"取消"}
              </Button>
              <Button variant="destructive" onClick={confirmDelete}>
                {"确认"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
        <Toaster />
      </div>
  );
}

export default App;
