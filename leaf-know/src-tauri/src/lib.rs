mod api_startup;
mod event_buffer;
use std::sync::{Arc, Mutex};
use tauri::Emitter;
use tauri::Manager;
use tauri::{
    // menu::{Menu, MenuItem, PredefinedMenuItem, Submenu},
    WindowEvent,
};
// use tokio::time::{sleep, Duration};

// 存储API进程的状态
struct ApiProcessState {
    process_child: Option<tauri_plugin_shell::process::CommandChild>,
    port: u16,
    host: String,
    db_path: String,
}

// API进程管理器，用于应用退出时自动清理资源
struct ApiProcessManager {
    api_state: Arc<Mutex<ApiProcessState>>,
}

impl ApiProcessManager {
    /// 实例清理方法，执行完整的清理逻辑
    pub fn cleanup(&self) {
        println!("执行ApiProcessManager完整清理");
        eprintln!("执行ApiProcessManager完整清理"); // 同时输出到 stderr

        // 尝试获取并终止 API 进程
        if let Ok(mut api_state) = self.api_state.lock() {
            if let Some(child) = api_state.process_child.take() {
                println!("通过实例方法终止 uv 和 Python API 进程树");

                // 由于使用 uv 启动，需要终止整个进程树
                // 先尝试获取进程ID用于进程树清理
                let child_pid = child.pid();
                println!("uv 进程 PID: {}", child_pid);

                // 尝试终止 uv 进程（这会终止直接子进程，但不一定终止孙进程）
                match child.kill() {
                    Ok(_) => {
                        println!("发送终止信号到 uv 进程成功");

                        // 等待短暂时间让进程响应信号
                        std::thread::sleep(std::time::Duration::from_millis(1000));
                    }
                    Err(e) => {
                        eprintln!("终止 uv 进程失败: {}", e);
                    }
                }

                println!("API 进程树终止完成");
            } else {
                println!("没有需要终止的 API 进程");
            }
        } else {
            eprintln!("无法获取 API 状态互斥锁");
        }

        // 执行静态清理作为后备
        Self::cleanup_processes_static();
    }

    /// 静态清理方法，可以在任何地方调用（后备清理）
    pub fn cleanup_processes() {
        Self::cleanup_processes_static();
    }

    /// 静态清理的实际实现
    fn cleanup_processes_static() {
        println!("执行静态进程清理");
        eprintln!("执行静态进程清理"); // 同时输出到 stderr

        // 在Unix系统上，强制清理所有相关的进程
        #[cfg(unix)]
        {
            println!("开始强制清理所有相关的 uv 和 Python 进程");

            // 使用多种模式确保清理干净，包括 uv 进程
            let cleanup_patterns = [
                "uv run --directory",
                "main.py --host 127.0.0.1 --port 60000",
                "/core/main.py",
            ];

            for pattern in &cleanup_patterns {
                println!("清理模式: {}", pattern);

                // 先发送SIGTERM
                match std::process::Command::new("pkill")
                    .args(["-f", pattern])
                    .status()
                {
                    Ok(status) => {
                        println!("SIGTERM 发送结果: {:?}", status);
                    }
                    Err(e) => {
                        println!("SIGTERM 发送失败: {}", e);
                    }
                }

                // 等待一秒后发送SIGKILL
                std::thread::sleep(std::time::Duration::from_millis(1000));
                match std::process::Command::new("pkill")
                    .args(["-9", "-f", pattern])
                    .status()
                {
                    Ok(status) => {
                        println!("SIGKILL 发送结果: {:?}", status);
                    }
                    Err(e) => {
                        println!("SIGKILL 发送失败: {}", e);
                    }
                }
            }

            println!("静态进程清理完成");
            eprintln!("静态进程清理完成");
        }
    }
}

// 实现 Drop trait，在应用退出时自动终止 API 进程
impl Drop for ApiProcessManager {
    fn drop(&mut self) {
        println!("应用程序退出，ApiProcessManager.drop() 被调用");
        eprintln!("应用程序退出，ApiProcessManager.drop() 被调用"); // 同时输出到 stderr

        // 调用实例清理方法
        self.cleanup();
    }
}

// API状态包装为线程安全类型
struct ApiState(Arc<Mutex<ApiProcessState>>);



#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_log::Builder::new()
                .level(tauri_plugin_log::log::LevelFilter::Info)
                .level_for("tao", log::LevelFilter::Warn) // 将 tao crate 的日志级别设为 Warn
                .level_for("notify", log::LevelFilter::Info) // Revert to INFO or desired level
                .build(),
        )
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_window_state::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_single_instance::init(|app, args, cwd| {
            println!(
                "另一个实例已尝试启动，参数: {:?}，工作文件夹: {}",
                args, cwd
            );
            // 使已经运行的窗口获得焦点
            if let Some(window) = app.get_webview_window("main") {
                window.show().unwrap();
                window.set_focus().unwrap();
            }
        }))
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_macos_permissions::init())
        .plugin(tauri_plugin_screenshots::init())
        .setup(|app| {
            let app_handle = app.handle();
            let api_state_instance = app.state::<ApiState>();

            // 创建 ApiProcessManager 并注册到应用，用于应用退出时自动清理 API 进程
            let api_manager = ApiProcessManager {
                api_state: api_state_instance.0.clone(),
            };
            app_handle.manage(api_manager);
            println!("已注册 ApiProcessManager，将在应用退出时自动清理 API 进程");

            // 注册全局 panic hook 用于清理
            let prev_hook = std::panic::take_hook();
            std::panic::set_hook(Box::new(move |panic_info| {
                println!("Panic detected, executing cleanup: {:?}", panic_info);
                ApiProcessManager::cleanup_processes();
                prev_hook(panic_info);
            }));

            // Start the Python API service automatically
            let db_path_str = app_handle
                .path()
                .app_data_dir()
                .map_err(|e| e.to_string())?
                .join("knowledge-focus.db")
                .to_string_lossy()
                .to_string();
            {
                // Scope for MutexGuard
                let mut api_state_guard = api_state_instance.0.lock().unwrap();
                api_state_guard.port = 60000;
                api_state_guard.host = "127.0.0.1".to_string();
                api_state_guard.db_path = db_path_str;
            }

            // 启动Python API
            let app_handle_for_api = app_handle.clone();
            let api_state_for_api = api_state_instance.0.clone();

            // 创建一个通信通道，实现API就绪后再开始文件监控
            let (tx, rx) = tokio::sync::oneshot::channel::<bool>();
            let tx = Arc::new(Mutex::new(Some(tx)));

            // 启动Python API服务
            tauri::async_runtime::spawn(async move {
                let tx_for_api = Arc::clone(&tx);

                // 调用api_startup模块中的start_python_api函数
                // 但我们不使用它返回的接收端，因为我们已经创建了自己的通信通道
                let _ = crate::api_startup::start_python_api(
                    app_handle_for_api.clone(),
                    api_state_for_api.clone(),
                );

                // 获取API主机和端口
                let (api_host, api_port) = {
                    let api_state_guard = api_state_for_api.lock().unwrap();
                    (api_state_guard.host.clone(), api_state_guard.port)
                };

                // 构建API健康检查URL
                let api_url = format!("http://{}:{}/health", api_host, api_port);
                println!("开始检查API是否就绪，API健康检查地址: {}", api_url);

                // 使用reqwest客户端检查API健康状态
                let client = reqwest::Client::new();
                let max_retries = 10000; // 最多尝试次数，足够长让用户看到详细日志
                let retry_interval = std::time::Duration::from_millis(1000); // 毫秒
                let mut api_ready = false;

                for i in 0..max_retries {
                    // 首先检查API进程是否运行
                    let api_running = {
                        let api_state_guard = api_state_for_api.lock().unwrap();
                        api_state_guard.process_child.is_some()
                    };

                    if !api_running {
                        // 如果进程不存在，等待短暂时间后再次检查
                        tokio::time::sleep(retry_interval).await;
                        continue;
                    }

                    // 尝试访问API健康检查端点
                    match client
                        .get(&api_url)
                        .timeout(std::time::Duration::from_secs(1))
                        .send()
                        .await
                    {
                        Ok(response) if response.status().is_success() => {
                            println!("第{}次尝试: API健康检查成功，API已就绪", i + 1);
                            api_ready = true;
                            break;
                        }
                        _ => {
                            // API尚未准备好，等待后重试
                            if (i + 1) % 5 == 0 {
                                // 每5次打印一次，避免日志过多
                                println!("第{}次尝试: API尚未就绪，继续等待...", i + 1);
                            }
                            tokio::time::sleep(retry_interval).await;
                        }
                    }
                }

                // 简化的 API 就绪信号发送逻辑
                // 发送信号到内部通道 (用于文件监控启动等)
                let _api_ready_sent = {
                    let mut lock = tx_for_api.lock().unwrap();
                    if let Some(sender) = lock.take() {
                        let send_result = sender.send(api_ready);
                        println!("已发送内部API就绪信号: {}", api_ready);
                        send_result.is_ok() && api_ready
                    } else {
                        false
                    }
                };

                // API 就绪时发送给主窗口，简化了条件检查
                if api_ready {
                    println!("Python API 已完全就绪，向主窗口发送 API 就绪信号");

                    // 获取主窗口句柄并发送就绪事件
                    if let Some(main) = app_handle_for_api.get_webview_window("main") {
                        // 向主窗口发送 API 就绪事件，这里是唯一发送位置
                        let _ = main.emit("api-ready", true);
                        println!("已向主窗口发送 API 就绪信号");
                    } else {
                        eprintln!("找不到主窗口，无法发送 API 就绪信号");
                    }
                }
            });

            // 等待API就绪信号后再准备文件监控基础设施
            let app_handle_for_monitor = app_handle.clone();
            // let api_state_for_monitor = api_state_instance.0.clone();

            tauri::async_runtime::spawn(async move {
                // 等待API就绪信号
                match rx.await {
                    Ok(true) => {
                        println!("收到API就绪信号");
                    }
                    _ => {
                        eprintln!("API未能成功启动，无法初始化文件监控基础设施");
                        if let Some(window) = app_handle_for_monitor.get_webview_window("main") {
                            let _ =
                                window.emit("file-monitor-error", "API未就绪，无法初始化文件监控");
                        }
                    }
                }
            });

            Ok(())
        })
        // 管理API进程状态
        .manage(ApiState(Arc::new(Mutex::new(ApiProcessState {
            process_child: None,
            port: 60000,
            host: "127.0.0.1".to_string(),
            db_path: String::new(),
        }))))
        .invoke_handler(tauri::generate_handler![
            
        ])
        .on_window_event(|window, event| match event {
            WindowEvent::Destroyed => {
                // 获取窗口的标牌，区分是哪个窗口被销毁
                let window_label = window.label();

                println!("窗口被销毁: {}", window_label);

                // 如果是主窗口被销毁，执行清理
                if window_label == "main" {
                    println!("主窗口被销毁，执行完整进程清理");

                    // 尝试获取ApiProcessManager并执行完整清理
                    if let Some(api_manager) = window.app_handle().try_state::<ApiProcessManager>()
                    {
                        api_manager.cleanup();
                        println!("通过ApiProcessManager实例执行了完整清理");
                    } else {
                        println!("无法获取ApiProcessManager，使用静态清理");
                        ApiProcessManager::cleanup_processes();
                    }
                }
            }
            WindowEvent::CloseRequested { api, .. } => {
                // 获取窗口的标牌，用于区分不同窗口
                let window_label = window.label();

                // 针对不同窗口采取不同的关闭策略
                match window_label {
                    // 对于主窗口，使用隐藏而不是关闭的逻辑
                    "main" => {
                        #[cfg(target_os = "macos")]
                        {
                            // Prevent the default window close behavior
                            api.prevent_close();
                            // Hide the window
                            println!("隐藏主窗口而不是关闭");
                            window.hide().unwrap();
                            let _ = window
                                .app_handle()
                                .set_activation_policy(tauri::ActivationPolicy::Accessory);
                        }
                        #[cfg(not(target_os = "macos"))]
                        {
                            // On other OS, default behavior is usually fine (exit/hide based on config),
                            // but explicitly exiting might be desired if default is hide.
                            window.app_handle().exit(0);
                        }
                    }
                    // 对于其他窗口，采用默认行为
                    _ => {
                        println!("关闭其他窗口: {}", window_label);
                    }
                }
            }
            _ => {}
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        .run(|app_handle, event| {
            // 获取事件名称用于调试
            let event_name = match &event {
                tauri::RunEvent::ExitRequested { .. } => "ExitRequested",
                tauri::RunEvent::Exit => "Exit",
                tauri::RunEvent::WindowEvent { event, .. } => match event {
                    tauri::WindowEvent::CloseRequested { .. } => "WindowEvent::CloseRequested",
                    tauri::WindowEvent::Destroyed => "WindowEvent::Destroyed",
                    _ => "WindowEvent::Other",
                },
                _ => "Other",
            };

            // 只在重要事件时打印，减少输出噪音
            if matches!(
                event,
                tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit
            ) {
                println!("=== 收到重要运行事件: {} ===", event_name);
            }

            match event {
                tauri::RunEvent::ExitRequested { .. } => {
                    // 应用退出请求时终止API进程
                    println!("ExitRequested 事件：开始清理API进程");

                    // 尝试获取ApiProcessManager并执行完整清理
                    if let Some(api_manager) = app_handle.try_state::<ApiProcessManager>() {
                        api_manager.cleanup();
                        println!("通过ApiProcessManager实例执行了完整清理");
                    } else {
                        println!("无法获取ApiProcessManager，使用静态清理");
                        ApiProcessManager::cleanup_processes();
                    }

                    println!("ExitRequested 事件：资源清理完毕");
                }
                tauri::RunEvent::Exit => {
                    // 应用最终退出时的备用清理
                    println!("Exit 事件：进行备用API进程清理");
                    ApiProcessManager::cleanup_processes();
                    println!("Exit 事件：备用清理完毕");
                }
                _ => {
                    // 其他事件不做处理
                }
            }
        });
}
