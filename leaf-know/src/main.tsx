import React from "react";
import ReactDOM from "react-dom/client";
import { create } from 'zustand';
import { load } from '@tauri-apps/plugin-store';
import { 
  // resourceDir, 
  join, 
  appDataDir 
} from '@tauri-apps/api/path';
import App from "./App";

interface AppGlobalState {
  // API readiness state
  isApiReady: boolean;
  setApiReady: (ready: boolean) => void;
}

// 创建 Zustand store
export const useAppStore = create<AppGlobalState>((set, _get) => ({
  isApiReady: false,
  setApiReady: (ready: boolean) => set({ isApiReady: ready }),
}));

const initializeApp = async () => {
  try {
    const appDataPath = await appDataDir();
    const storePath = await join(appDataPath, 'settings.json');
    const store = await load(storePath, { defaults: { language: 'en' }, autoSave: false });
    const savedLanguage = await store.get('language') as string | null;
    const language = savedLanguage || 'en'; // 如果没有保存语言设置，默认使用英文
    console.log(`应用语言设置为: ${language}`);
    
     // Set initial Zustand states based on whether it's the first launch
    useAppStore.setState({ 
      isApiReady: false,     // API is not ready at this point
    });

   
    // 渲染应用
    ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  } catch (error) {
    console.error('Failed to initialize app:', error);
  }
};

// 启动应用
initializeApp();

document.addEventListener("DOMContentLoaded", () => {
  const dragRegionDiv = document.createElement("div");
  dragRegionDiv.setAttribute("data-tauri-drag-region", "");
  dragRegionDiv.className = "dragble-state";
  document.documentElement.insertBefore(dragRegionDiv, document.body);
});