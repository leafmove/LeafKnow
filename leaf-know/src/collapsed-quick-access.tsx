import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { MessageCircle } from "lucide-react"
import { ChatSession } from "./lib/chat-session-api"

interface CollapsedQuickAccessProps {
  sessions: ChatSession[]
  onSessionClick: (session: ChatSession) => void
}

export function CollapsedQuickAccess({ 
  sessions, 
  onSessionClick 
}: CollapsedQuickAccessProps) {


  // 获取Top10对话（按时间排序，和展开状态一致）
  const topSessions = sessions.slice(0, 10)

  return (
    <div className="flex flex-col h-full justify-start items-center pl-1">
        <div className="space-y-1">
          <Separator className="bg-border my-4" />
          

          {/* 对话Top10区域 */}
          {topSessions.length > 0 && (
            <div className="space-y-1">
              {/* 分组标题 */}
              <div className="flex items-center justify-center">
                <MessageCircle className="size-4" />
              </div>
              
              {/* 对话按钮列表 */}
              <div className="space-y-1">
                {topSessions.map((session, index) => (
                  <Tooltip key={session.id} delayDuration={0}>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="size-5 p-0 text-xs font-medium justify-center "
                        onClick={() => onSessionClick(session)}
                      >
                        <span className="font-semibold">
                          {index + 1}
                        </span>
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      <div className="text-sm">
                        <div className="font-medium line-clamp-2">{session.name}</div>
                        <div className="text-xs">
                          {new Date(session.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                ))}
              </div>
            </div>
          )}
        </div>
    </div>
  )
}
