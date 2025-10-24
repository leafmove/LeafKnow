import React, { useState, useEffect } from 'react';
import { useAppStore } from '@/main';
import { Button } from "./components/ui/button";
import { toast } from "sonner";
// import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { 
  checkFullDiskAccessPermission, 
  requestFullDiskAccessPermission 
} from "tauri-plugin-macos-permissions-api";
import { relaunch } from '@tauri-apps/plugin-process';
import { RagLocal } from './rag-local';

interface SplashProps {
  setShowSplash: (showSplash: boolean) => void;
}

const Splash: React.FC<SplashProps> = ({setShowSplash: setShowSplash }) => {
  // 使用 selector 获取 Zustand store 中的状态，避免不必要的重渲染
  const isApiReady = useAppStore(state => state.isApiReady);
  const [loading, setLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState("Checking permissions...");
  const [hasFullDiskAccess, setHasFullDiskAccess] = useState(false);
  const [checkingPermission, setCheckingPermission] = useState(true);
  const [permissionRequested, setPermissionRequested] = useState(false);
  
  // API 错误状态（用于控制 RagLocal 显示）
  const [hasApiError, setHasApiError] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  
  // 检查完全磁盘访问权限
  const checkFullDiskAccess = async () => {
    try {
      setCheckingPermission(true);
      setLoadingMessage("正在检查完全磁盘访问权限...");
      
      // 使用tauri-plugin-macos-permissions-api检查权限
      const permission = await checkFullDiskAccessPermission();
      // console.log("[权限检查] 完全磁盘访问权限状态:", permission);
      setHasFullDiskAccess(!!permission);
      
      if (permission) {
        setLoadingMessage("权限验证通过，正在等待后端程序就绪...");
        // console.log("[权限检查] 权限检查通过，等待API就绪后自动启动后端扫描");
      } else {
        setLoadingMessage("需要完全磁盘访问权限才能继续使用应用");
        // console.log("[权限检查] 权限未获得，阻止进入应用");
      }
      
      return !!permission;
    } catch (error) {
      console.error("[权限检查] 检查完全磁盘访问权限失败:", error);
      setLoadingMessage("权限检查失败，请重启应用");
      toast.error("权限检查失败，请重启应用");
      setHasFullDiskAccess(false);
      return false;
    } finally {
      setCheckingPermission(false);
    }
  };

  // 请求完全磁盘访问权限
  const requestFullDiskAccess = async () => {
    try {
      setCheckingPermission(true);
      setLoadingMessage("正在请求完全磁盘访问权限...");
      
      // 使用tauri-plugin-macos-permissions-api请求权限
      const result = await requestFullDiskAccessPermission();
      console.log("[权限请求] 请求结果:", result);
      
      // 标记已请求权限，这将改变按钮行为
      setPermissionRequested(true);
      
      // 提供明确的授权指导
      toast.success(
        "请在系统设置中授权:\n1. 点击'系统设置' > '隐私与安全性'\n2. 选择'完全磁盘访问权限'\n3. 勾选'Leaf Know'应用\n4. 授权完成后点击'重启App'按钮", 
        { duration: 10000 }
      );
      
      setLoadingMessage("请在系统设置中授予完全磁盘访问权限后重启应用");
      
      // 延迟检查权限状态 - 用户可能在系统设置中立即授予权限
      const checkPermissionWithDelay = async () => {
        // 等待用户可能在系统设置中进行的操作
        // console.log("[权限请求] 延迟3秒后重新检查权限状态");
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // 重新检查权限
        const hasPermissionNow = await checkFullDiskAccess();
        if (hasPermissionNow) {
          // console.log("[权限请求] 重新检查发现权限已授予");
          toast.success("权限已成功获取！正在初始化系统...");
        } else {
          // console.log("[权限请求] 重新检查后权限仍未授予");
          // 用户可能需要重启应用以使权限生效
          toast.info("如果您已授予权限但未生效，请重启应用", { duration: 8000 });
        }
      };
      
      // 执行延迟检查
      checkPermissionWithDelay();
      
    } catch (error) {
      console.error("[权限请求] 请求完全磁盘访问权限失败:", error);
      toast.error("权限请求失败，请手动在系统设置中开启权限");
      
      // 即使出错也给出明确的手动操作指南
      toast.info(
        "请在系统设置中授权:\n1. 点击'系统设置' > '隐私与安全性'\n2. 选择'完全磁盘访问权限'\n3. 勾选'Leaf Know'应用\n4. 授权完成后点击'重启App'按钮", 
        { duration: 10000 }
      );
    } finally {
      setCheckingPermission(false);
    }
  };
  
  // 初始化时不再检查权限，让 uv 和 API 并行启动
  // 权限检查延后到模型下载成功后进行
  useEffect(() => {
    // 设置初始加载状态，等待API就绪
    setLoading(true);
    setLoadingMessage("Initializing...");
  }, []);
  
  // 监听 API 日志和错误事件（用于控制日志显示）
  useEffect(() => {
    let apiLogUnlisten: (() => void) | null = null;
    let apiErrorUnlisten: (() => void) | null = null;
    let isMounted = true;
    
    const setupApiListeners = async () => {
      try {
        // 监听 API 日志（用于显示日志窗口）
        apiLogUnlisten = await listen<string>('api-log', (event) => {
          if (!isMounted) return;
          
          // console.log('[Splash] 收到 api-log 事件:', event.payload);
          
          // 收到任何 API 日志就显示日志窗口
          if (event.payload) {
            setShowLogs(true);
          }
        });
        
        console.log('[Splash] API 日志监听器已设置');
        
        // 监听 API 错误（用于显示错误提示）
        apiErrorUnlisten = await listen<string>('api-error', (event) => {
          if (!isMounted) return;
          
          // console.log('[Splash] 收到 api-error 事件:', event.payload);
          
          if (event.payload && event.payload.trim()) {
            setHasApiError(true);
            setShowLogs(true);
            setLoadingMessage('API 启动过程中出现错误，请查看详细日志');
          }
        });
        
        console.log('[Splash] API 错误监听器已设置');
      } catch (error) {
        if (isMounted) {
          console.error('设置 API 监听器失败:', error);
        }
      }
    };
    
    setupApiListeners();
    
    return () => {
      isMounted = false;
      if (apiLogUnlisten) {
        apiLogUnlisten();
      }
      if (apiErrorUnlisten) {
        apiErrorUnlisten();
      }
    };
  }, []);
  
  // API就绪后检查（无需等待权限）
  useEffect(() => {
    console.log(`[Splash] API就绪状态变化: isApiReady=${isApiReady}`);
    
    if (!isApiReady) {
      console.log('[Splash] API未就绪，等待中...');
      return;
    }
    
    console.log('[Splash] API已就绪');
    checkPermissionAndStartScan();
    
  }, [isApiReady]);
  
  
  // 权限检查和后端扫描函数
  const checkPermissionAndStartScan = async () => {
    try {
      // 检查磁盘访问权限
      setLoadingMessage("Checking disk access permission...");
      setCheckingPermission(true);
      
      const permission = await checkFullDiskAccessPermission();
      setHasFullDiskAccess(!!permission);
      setCheckingPermission(false);
      
      if (!permission) {
        // 权限未授予，停止loading，显示请求权限按钮
        setLoading(false);
        setLoadingMessage("Disk access permission required");
        return;
      }

      // 权限通过
      setLoading(false);
      setLoadingMessage("初始化完成，正在进入应用...");
      
      setTimeout(() => {
        setShowSplash(false);
      }, 800);
      
      
    } catch (error) {
      console.error("权限检查失败:", error);
      setCheckingPermission(false);
      setHasFullDiskAccess(false);
      setLoading(false);
      setLoadingMessage("Permission check failed");
      toast.error("Failed to check disk access permission");
    }
  };
  
  

  return (
    <div className="flex flex-col items-center justify-center max-w-md mx-auto h-screen p-5">
      <div>
        <div className="text-2xl font-bold text-center">{"欢迎使用Leaf Know"}</div>
        <div className="text-center">
          {"Leaf Know 是一个好玩的AI伴读App。"}
        </div>
      </div>
      
      {/* 加载指示器容器 - 固定高度防止布局跳动 */}
      <div className="h-20 flex justify-center items-center my-4">
        {(loading || checkingPermission) && (
          <div className="relative w-12 h-12">
            <svg className="animate-spin" viewBox="0 0 24 24" fill="none" stroke="#D29B71" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="2" x2="12" y2="6"></line>
              <line x1="12" y1="18" x2="12" y2="22"></line>
              <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
              <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
              <line x1="2" y1="12" x2="6" y2="12"></line>
              <line x1="18" y1="12" x2="22" y2="12"></line>
              <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
              <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
            </svg>
          </div>
        )}
        
        {/* 权限状态图标 */}
        {!loading && !checkingPermission && (
          <div className={`flex items-center justify-center p-3 rounded-full ${hasFullDiskAccess ? 'bg-green-100' : 'bg-yellow-100'}`}>
            {hasFullDiskAccess ? (
              <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
            ) : (
              <svg className="w-10 h-10 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
              </svg>
            )}
          </div>
        )}
      </div>
      
      <p className={`text-center mb-4 ${
        hasFullDiskAccess && isApiReady 
          ? "text-green-600" 
          : !hasFullDiskAccess 
            ? "text-yellow-600 font-semibold" 
            : "text-whiskey-700 animate-pulse"
      }`}>
        {loadingMessage}
      </p>
      
      
      
      {/* API 启动日志显示区域 */}
      {showLogs && (
        <div className="w-full mb-4">
          {/* 使用统一的 RagLocal 组件显示 API 启动日志 - 限制高度 */}
          <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-md bg-gray-50">
            <RagLocal 
              mode="startup-only"
              showHeader={false}
            />
          </div>
          
          {/* 如果有错误，显示文档链接 */}
          {hasApiError && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-700 mb-2">
                API 启动过程中出现错误，可能是网络连接问题导致依赖包下载失败。
              </p>
              <a 
                href="https://kf.huozhong.in/doc" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800 underline font-medium"
              >
                📖 查看解决方案文档
              </a>
            </div>
          )}
        </div>
      )}
      
      {/* 权限说明 */}
      {!hasFullDiskAccess && !checkingPermission && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
          <p className="text-sm text-yellow-700 mb-2">
            {"请授予完全磁盘访问权限以确保应用正常运行。"}
          </p>
          <p className="text-sm text-yellow-700">
            {"请在系统设置中授权:\n1. 点击'系统设置' > '隐私与安全性'\n2. 选择'完全磁盘访问权限'\n3. 勾选'Leaf Know'应用\n4. 授权完成后点击'重启App'按钮"}
          </p>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-2 sm:gap-0">          
        {/* 未获得权限时显示请求权限按钮或重启App按钮 */}
        {!hasFullDiskAccess && !checkingPermission && (
          <Button
            onClick={permissionRequested ? () => relaunch() : requestFullDiskAccess}
            className={`w-full sm:w-auto text-white ${permissionRequested ? 'bg-green-600 hover:bg-green-700' : 'bg-yellow-600 hover:bg-yellow-700'} rounded-lg`}
          >
            {permissionRequested ? "重启App" : "请求磁盘访问权限"}
          </Button>
        )}
      </div>
    </div>
  )
};

export default Splash;