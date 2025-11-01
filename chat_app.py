#!/usr/bin/env python3
"""
基于ttkbootstrap的AI聊天客户端GUI应用
支持多会话管理、Agent管理、流式聊天
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
try:
    import ttkbootstrap as ttb
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    print("ttkbootstrap未安装，请运行: pip install ttkbootstrap")
    TTKBOOTSTRAP_AVAILABLE = False
    ttb = None
import threading
import queue
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

# 导入核心模块
from core.agent.chat_engine import (
    DatabaseManager, UserManager, AgentManager, SessionManager,
    ConversationManager, AgentConfig, DatabaseType,
    Agent, OpenAIChat, OPENAI_AVAILABLE, OpenRouter, OPENROUTER_AVAILABLE,
    Ollama, OLLAMA_AVAILABLE, LlamaCpp, LLAMACPP_AVAILABLE
)


class ChatBubble(tk.Frame):
    """聊天气泡组件"""

    def __init__(self, parent, message: str, role: str, timestamp: str = None, **kwargs):
        super().__init__(parent, **kwargs)

        self.role = role
        self.message = message
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        self.msg_label = None  # 用于后续更新消息内容

        # 设置样式
        self.configure(bg="#f0f0f0")

        # 创建主容器
        main_frame = tk.Frame(self, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 根据角色决定对齐方式
        if role == "user":
            # 用户消息右对齐
            right_container = tk.Frame(main_frame, bg="#f0f0f0")
            right_container.pack(side=tk.RIGHT, fill=tk.X, expand=True)

            # 时间戳和角色（顶部小字）
            info_frame = tk.Frame(right_container, bg="#f0f0f0")
            info_frame.pack(fill=tk.X, anchor="e")

            role_label = tk.Label(
                info_frame,
                text="用户",
                bg="#f0f0f0",
                fg="#007bff",
                font=("Microsoft YaHei UI", 7)
            )
            role_label.pack(side=tk.RIGHT, padx=(0, 5))

            time_label = tk.Label(
                info_frame,
                text=self.timestamp,
                bg="#f0f0f0",
                fg="#999999",
                font=("Microsoft YaHei UI", 7)
            )
            time_label.pack(side=tk.RIGHT, padx=(0, 8))

            # 消息气泡
            bubble_frame = tk.Frame(right_container, bg="#007bff", relief=tk.RAISED, bd=1)
            bubble_frame.pack(fill=tk.X, pady=(2, 0), padx=(50, 0))

            # 消息内容
            self.msg_label = tk.Label(
                bubble_frame,
                text=message,
                bg="#007bff",
                fg="white",
                wraplength=400,  # 减少wraplength避免超出显示区域
                justify=tk.LEFT,
                font=("Microsoft YaHei UI", 10)
            )
            self.msg_label.pack(padx=12, pady=10, anchor="w")

        else:
            # AI消息左对齐
            left_container = tk.Frame(main_frame, bg="#f0f0f0")
            left_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # 时间戳和角色（顶部小字）
            info_frame = tk.Frame(left_container, bg="#f0f0f0")
            info_frame.pack(fill=tk.X, anchor="w")

            role_label = tk.Label(
                info_frame,
                text="助手",
                bg="#f0f0f0",
                fg="#28a745",
                font=("Microsoft YaHei UI", 7)
            )
            role_label.pack(side=tk.LEFT, padx=(5, 0))

            time_label = tk.Label(
                info_frame,
                text=self.timestamp,
                bg="#f0f0f0",
                fg="#999999",
                font=("Microsoft YaHei UI", 7)
            )
            time_label.pack(side=tk.LEFT, padx=(8, 0))

            # 消息气泡
            bubble_frame = tk.Frame(left_container, bg="white", relief=tk.RAISED, bd=1)
            bubble_frame.pack(fill=tk.X, pady=(2, 0), padx=(0, 50))

            # 消息内容
            self.msg_label = tk.Label(
                bubble_frame,
                text=message,
                bg="white",
                fg="black",
                wraplength=400,  # 减少wraplength避免超出显示区域
                justify=tk.LEFT,
                font=("Microsoft YaHei UI", 10)
            )
            self.msg_label.pack(padx=12, pady=10, anchor="w")

    def update_message(self, text: str):
        """更新消息内容"""
        if self.msg_label:
            self.msg_label.configure(text=text)
            self.message = text


class SessionListFrame(ttb.Frame):
    """会话列表框架"""

    def __init__(self, parent, chat_app, **kwargs):
        super().__init__(parent, **kwargs)
        self.chat_app = chat_app

        # 标题
        title_frame = tk.Frame(self)
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(title_frame, text="聊天会话", font=("Microsoft YaHei UI", 12, "bold")).pack(side=tk.LEFT)

        # 新建会话按钮
        if ttb:
            self.new_session_btn = ttb.Button(
                title_frame,
                text="+",
                bootstyle=SUCCESS,
                width=3,
                command=self.new_session
            )
        else:
            self.new_session_btn = tk.Button(
                title_frame,
                text="+",
                bg="#28a745",
                fg="white",
                width=3,
                command=self.new_session
            )
        self.new_session_btn.pack(side=tk.RIGHT)

        # 会话列表
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建滚动区域
        canvas = tk.Canvas(list_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.session_list_frame = tk.Frame(canvas, bg="white")

        # 更新滚动区域
        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.session_list_frame.bind("<Configure>", update_scroll_region)

        # 创建canvas window并设置宽度
        canvas.create_window((0, 0), window=self.session_list_frame, anchor="nw", width=230)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定canvas大小变化事件
        def on_canvas_configure(event):
            # 更新frame宽度以匹配canvas宽度
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        self.session_widgets = []
        self.refresh_session_list()

    def refresh_session_list(self):
        """刷新会话列表"""
        # 清空现有组件
        for widget in self.session_widgets:
            widget.destroy()
        self.session_widgets.clear()

        # 获取会话列表
        sessions = self.chat_app.session_manager.get_user_sessions(self.chat_app.current_user_id)

        for session in sessions:
            # 创建会话项
            session_item = self.create_session_item(session)
            session_item.pack(fill=tk.X, pady=2)
            self.session_widgets.append(session_item)

    def create_session_item(self, session):
        """创建会话项组件"""
        item_frame = tk.Frame(self.session_list_frame, bg="white", relief=tk.RIDGE, bd=1, height=100)
        item_frame.pack_propagate(False)  # 防止子组件改变frame大小

        # 获取会话的Agent信息
        agent = None
        if session.current_agent_id:
            agent = self.chat_app.agent_manager.get_agent(session.current_agent_id)

        # 当前会话高亮
        if session.id == self.chat_app.current_session_id:
            item_frame.configure(bg="#e3f2fd")

        # 主内容区域
        content_frame = tk.Frame(item_frame, bg=item_frame["bg"])
        content_frame.pack(fill=tk.X, expand=True, padx=8, pady=5)

        # 会话标题
        title_text = session.title
        if len(title_text) > 20:  # 增加标题长度限制
            title_text = title_text[:20] + "..."

        title_label = tk.Label(
            content_frame,
            text=title_text,
            font=("Microsoft YaHei UI", 9, "bold" if session.id == self.chat_app.current_session_id else "normal"),
            bg=item_frame["bg"],
            fg="#1976d2" if session.id == self.chat_app.current_session_id else "black",
            anchor="w"
        )
        title_label.pack(fill=tk.X, pady=(0, 2))

        # Agent信息
        if agent:
            agent_label = tk.Label(
                content_frame,
                text=f"🤖 {agent.name[:12] + '...' if len(agent.name) > 12 else agent.name}",  # 增加agent名称长度
                font=("Microsoft YaHei UI", 7),
                bg=item_frame["bg"],
                fg="#666666",
                anchor="w"
            )
            agent_label.pack(fill=tk.X, pady=(0, 2))

        # 时间戳
        time_label = tk.Label(
            content_frame,
            text=session.updated_at.strftime("%m-%d %H:%M"),
            font=("Microsoft YaHei UI", 7),
            bg=item_frame["bg"],
            fg="#999999",
            anchor="w"
        )
        time_label.pack(fill=tk.X)

        # 按钮区域
        button_frame = tk.Frame(item_frame, bg=item_frame["bg"])
        button_frame.pack(fill=tk.X, padx=8, pady=(0, 5))

        # 重命名按钮
        rename_btn = tk.Button(
            button_frame,
            text="编辑",
            font=("Microsoft YaHei UI", 8, "bold"),
            bg="#ffc107",
            fg="white",
            relief=tk.RAISED,
            bd=1,
            padx=8,
            pady=4,
            command=lambda: self.rename_session(session),
            cursor="hand2"
        )
        rename_btn.pack(side=tk.LEFT, padx=(0, 3))

        # 清空按钮
        clear_btn = tk.Button(
            button_frame,
            text="清空",
            font=("Microsoft YaHei UI", 8, "bold"),
            bg="#17a2b8",
            fg="white",
            relief=tk.RAISED,
            bd=1,
            padx=8,
            pady=4,
            command=lambda: self.clear_session(session),
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=3)

        # 删除按钮 (只有非默认会话才显示删除按钮)
        if session.title != "默认会话":
            delete_btn = tk.Button(
                button_frame,
                text="删除",
                font=("Microsoft YaHei UI", 8, "bold"),
                bg="#dc3545",
                fg="white",
                relief=tk.RAISED,
                bd=1,
                padx=8,
                pady=4,
                command=lambda: self.delete_session(session),
                cursor="hand2"
            )
            delete_btn.pack(side=tk.LEFT, padx=3)

        # 绑定点击事件
        def on_click(event):
            self.chat_app.switch_to_session(session.id)

        # 绑定右键菜单
        def on_right_click(event):
            self.show_context_menu(event, session)

        # 绑定点击事件到内容区域，避免按钮点击时触发
        for widget in content_frame.winfo_children():
            widget.bind("<Button-1>", on_click)
        content_frame.bind("<Button-1>", on_click)
        item_frame.bind("<Button-1>", on_click)
        item_frame.bind("<Button-3>", on_right_click)

        return item_frame

    def show_context_menu(self, event, session):
        """显示右键菜单"""
        context_menu = tk.Menu(self, tearoff=0)

        if session.title != "默认会话":
            context_menu.add_command(
                label="重命名",
                command=lambda: self.rename_session(session)
            )

        context_menu.add_command(
            label="清空会话",
            command=lambda: self.clear_session(session)
        )

        if session.title != "默认会话" and len(self.chat_app.session_manager.get_user_sessions(self.chat_app.current_user_id)) > 1:
            context_menu.add_command(
                label="删除会话",
                command=lambda: self.delete_session(session)
            )

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def new_session(self):
        """新建会话"""
        dialog = SessionDialog(self, self.chat_app)
        dialog.title("新建会话")
        self.wait_window(dialog)

        if dialog.result:
            # 切换到新会话
            self.chat_app.switch_to_session(dialog.result['session_id'])
            self.refresh_session_list()

    def rename_session(self, session):
        """重命名会话"""
        new_title = simpledialog.askstring(
            "重命名会话",
            f"请输入新的会话名称：",
            initialvalue=session.title,
            parent=self
        )

        if new_title and new_title != session.title:
            if self.chat_app.session_manager.update_session(session.id, title=new_title):
                self.refresh_session_list()
            else:
                messagebox.showerror("错误", "重命名失败")

    def clear_session(self, session):
        """清空会话"""
        result = messagebox.askyesno(
            "确认清空",
            f"确定要清空会话「{session.title}」的所有对话记录吗？\n此操作不可撤销！",
            parent=self
        )

        if result:
            if self.chat_app.conversation_manager.clear_conversation_history(session.id):
                if session.id == self.chat_app.current_session_id:
                    self.chat_app.refresh_chat_display()
                messagebox.showinfo("成功", "会话已清空")
            else:
                messagebox.showerror("错误", "清空失败")

    def delete_session(self, session):
        """删除会话"""
        result = messagebox.askyesno(
            "确认删除",
            f"确定要删除会话「{session.title}」吗？\n此操作不可撤销！",
            parent=self
        )

        if result:
            if self.chat_app.session_manager.delete_session(session.id):
                # 如果删除的是当前会话，切换到默认会话
                if session.id == self.chat_app.current_session_id:
                    sessions = self.chat_app.session_manager.get_user_sessions(self.chat_app.current_user_id)
                    if sessions:
                        self.chat_app.switch_to_session(sessions[0].id)

                self.refresh_session_list()
                messagebox.showinfo("成功", "会话已删除")
            else:
                messagebox.showerror("错误", "删除失败")


class ChatDisplayFrame(ttb.Frame):
    """聊天显示框架"""

    def __init__(self, parent, chat_app, **kwargs):
        super().__init__(parent, **kwargs)
        self.chat_app = chat_app

        # 创建滚动区域
        self.canvas = tk.Canvas(self, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.chat_frame = tk.Frame(self.canvas, bg="#f0f0f0")

        self.chat_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind("<MouseWheel>", _on_mousewheel)

        self.bubbles = []

        # 延迟显示，等待会话初始化完成
        self.chat_app.root.after(100, self.refresh_display)

    def refresh_display(self):
        """刷新聊天显示"""
        # 清空现有气泡
        for bubble in self.bubbles:
            bubble.destroy()
        self.bubbles.clear()

        if not self.chat_app.current_session_id:
            self.show_empty_state()
            return

        # 获取对话历史
        history = self.chat_app.conversation_manager.get_conversation_history(
            self.chat_app.current_session_id, 50
        )

        if not history:
            self.show_empty_state()
            return

        # 按时间顺序显示消息（最早的消息在前）
        for message in reversed(history):
            bubble = ChatBubble(
                self.chat_frame,
                message=message['content'],
                role=message['role'],
                timestamp=message.get('timestamp', '')
            )
            bubble.pack(fill=tk.X, pady=2)
            self.bubbles.append(bubble)

        # 滚动到底部
        self.scroll_to_bottom()

    def show_empty_state(self):
        """显示空状态"""
        empty_label = tk.Label(
            self.chat_frame,
            text="暂无对话记录\n开始你的第一次对话吧！",
            font=("Microsoft YaHei UI", 12),
            bg="#f0f0f0",
            fg="#999999"
        )
        empty_label.pack(expand=True, pady=20)
        self.bubbles.append(empty_label)

    def add_message(self, message: str, role: str):
        """添加新消息"""
        # 移除空状态提示
        if len(self.bubbles) == 1 and isinstance(self.bubbles[0], tk.Label):
            self.bubbles[0].destroy()
            self.bubbles.clear()

        bubble = ChatBubble(
            self.chat_frame,
            message=message,
            role=role
        )
        bubble.pack(fill=tk.X, pady=2, padx=10)
        self.bubbles.append(bubble)

        # 滚动到底部
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """滚动到底部"""
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def clear_display(self):
        """清空显示"""
        for bubble in self.bubbles:
            bubble.destroy()
        self.bubbles.clear()
        self.show_empty_state()


class InputFrame(ttb.Frame):
    """输入框架"""

    def __init__(self, parent, chat_app, **kwargs):
        super().__init__(parent, **kwargs)
        self.chat_app = chat_app

        # 输入区域
        input_frame = tk.Frame(self)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 输入框
        self.input_text = tk.Text(
            input_frame,
            height=4,
            font=("Microsoft YaHei UI", 10),
            wrap=tk.WORD,
            relief=tk.FLAT,
            bd=1,
            padx=8,
            pady=8
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # 绑定Enter键发送（Ctrl+Enter换行）
        self.input_text.bind("<Control-Return>", lambda e: None)  # 允许Ctrl+Enter换行
        self.input_text.bind("<Return>", self.on_enter_pressed)

        # 按钮栏
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Agent选择按钮
        self.agent_button = ttb.Button(
            button_frame,
            text="选择Agent",
            bootstyle=INFO,
            command=self.show_agent_selector
        )
        self.agent_button.pack(side=tk.LEFT)

        self.update_agent_button_text()

        # 发送/停止按钮
        self.send_button = ttb.Button(
            button_frame,
            text="发送",
            bootstyle=SUCCESS,
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 当前状态
        self.is_generating = False
        self.current_thread = None

    def update_agent_button_text(self):
        """更新Agent按钮文本"""
        if self.chat_app.current_agent_id:
            agent = self.chat_app.agent_manager.get_agent(self.chat_app.current_agent_id)
            if agent:
                self.agent_button.configure(text=f"🤖 {agent.name}")
            else:
                self.agent_button.configure(text="选择Agent")
        else:
            self.agent_button.configure(text="选择Agent")

    def on_enter_pressed(self, event):
        """处理Enter键"""
        if not event.state & 0x4:  # 检查是否按下了Ctrl键
            self.send_message()
            return "break"
        return None

    def send_message(self):
        """发送消息"""
        if self.is_generating:
            # 停止生成
            self.stop_generation()
            return

        message = self.input_text.get("1.0", tk.END).strip()
        if not message:
            return

        # 检查是否有可用的Agent
        if not self.chat_app.current_agent_id:
            messagebox.showwarning("警告", "请先选择一个Agent")
            return

        # 清空输入框
        self.input_text.delete("1.0", tk.END)

        # 添加用户消息到显示
        self.chat_app.chat_display.add_message(message, "user")

        # 保存用户消息到数据库
        self.chat_app.conversation_manager.add_message(
            self.chat_app.current_session_id,
            self.chat_app.current_user_id,
            self.chat_app.current_agent_id,
            "user",
            message
        )

        # 更新会话时间戳
        self.chat_app.session_manager.update_session_timestamp(self.chat_app.current_session_id)

        # 开始AI回复
        self.start_ai_generation(message)

    def start_ai_generation(self, user_message: str):
        """开始AI生成"""
        self.is_generating = True
        self.send_button.configure(text="停止", bootstyle=DANGER)
        self.input_text.configure(state=tk.DISABLED)

        # 在主线程中预先获取Agent配置，避免在后台线程中访问数据库
        agent_config = None
        if self.chat_app.current_agent_id:
            agent_config = self.chat_app.agent_manager.get_agent(self.chat_app.current_agent_id)

        if not agent_config:
            self.chat_app.root.after(0, lambda: self.update_ai_bubble("[错误] 无法获取Agent配置"))
            self.chat_app.root.after(0, self.reset_generation_state)
            return

        # 创建流式回复气泡
        self.ai_bubble = ChatBubble(
            self.chat_app.chat_display.chat_frame,
            message="",
            role="assistant"
        )
        self.ai_bubble.pack(fill=tk.X, pady=2)
        self.chat_app.chat_display.bubbles.append(self.ai_bubble)

        # 在新线程中执行AI生成
        self.current_thread = threading.Thread(
            target=self.generate_ai_response,
            args=(user_message, agent_config),
            daemon=True
        )
        self.current_thread.start()

    def generate_ai_response(self, user_message: str, agent_config):
        """生成AI响应（在后台线程中执行）"""
        try:
            full_response = ""
            print(f"[调试] 开始生成AI响应，用户消息: {user_message[:50]}...")

            # 获取流式响应
            chunk_count = 0
            for chunk in self.chat_app.chat_streaming_with_config(user_message, agent_config):
                if not self.is_generating:  # 检查是否被停止
                    print(f"[调试] 用户停止生成")
                    break

                if chunk:
                    chunk_count += 1
                    full_response += chunk
                    print(f"[调试] 收到chunk {chunk_count}: {chunk[:20]}...")
                    # 更新UI（需要在主线程中执行）
                    self.chat_app.root.after(0, self.update_ai_bubble, full_response)

            print(f"[调试] AI响应生成完成，总共{chunk_count}个chunk，长度: {len(full_response)}")

            # 在主线程中保存完整的AI回复到数据库
            if full_response.strip():
                self.chat_app.root.after(0, lambda: self.save_ai_response(full_response.strip()))
                print(f"[调试] AI回复已安排保存到数据库")

        except Exception as e:
            print(f"[调试] AI生成异常: {str(e)}")
            import traceback
            traceback.print_exc()
            error_message = f"[错误] AI生成失败: {str(e)}"
            self.chat_app.root.after(0, self.update_ai_bubble, error_message)

        finally:
            # 重置状态
            self.chat_app.root.after(0, self.reset_generation_state)

    def update_ai_bubble(self, text: str):
        """更新AI气泡内容"""
        if hasattr(self, 'ai_bubble') and self.ai_bubble:
            # 直接使用ChatBubble的update_message方法
            self.ai_bubble.update_message(text)
            # 滚动到底部
            self.chat_app.chat_display.scroll_to_bottom()

    def save_ai_response(self, response_text: str):
        """在主线程中保存AI响应到数据库"""
        try:
            self.chat_app.conversation_manager.add_message(
                self.chat_app.current_session_id,
                self.chat_app.current_user_id,
                self.chat_app.current_agent_id,
                "assistant",
                response_text
            )
            print(f"[调试] AI回复已保存到数据库")
        except Exception as e:
            print(f"[调试] 保存AI回复失败: {str(e)}")

    def stop_generation(self):
        """停止生成"""
        self.is_generating = False
        self.reset_generation_state()

    def reset_generation_state(self):
        """重置生成状态"""
        self.is_generating = False
        self.send_button.configure(text="发送", bootstyle=SUCCESS)
        self.input_text.configure(state=tk.NORMAL)
        self.input_text.focus_set()

        # 滚动到底部
        self.chat_app.chat_display.scroll_to_bottom()

    def show_agent_selector(self):
        """显示Agent选择器"""
        dialog = AgentManagementDialog(self, self.chat_app)
        self.wait_window(dialog)

        # 刷新Agent按钮文本
        self.update_agent_button_text()




class AgentManagementDialog(ttb.Toplevel):
    """Agent管理对话框"""

    def __init__(self, parent, chat_app, **kwargs):
        super().__init__(parent, **kwargs)
        self.chat_app = chat_app

        self.title("Agent管理")
        self.geometry("900x600")
        self.resizable(True, True)

        # 居中显示
        self.center_window()
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # 加载Agent列表
        self.load_agents()

    def center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        """设置UI"""
        # 主框架
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题和按钮
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(
            title_frame,
            text="Agent管理",
            font=("Microsoft YaHei UI", 14, "bold")
        ).pack(side=tk.LEFT)

        ttk.Button(
            title_frame,
            text="新建Agent",
            command=self.create_agent,
            bootstyle=SUCCESS
        ).pack(side=tk.RIGHT)

        # 主内容区域（左右分布）
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧Agent列表
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建Treeview
        columns = ("name", "provider", "model", "local", "default", "actions")
        self.agent_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            height=15
        )

        # 设置列
        self.agent_tree.heading("#0", text="")
        self.agent_tree.heading("name", text="名称")
        self.agent_tree.heading("provider", text="提供商")
        self.agent_tree.heading("model", text="模型")
        self.agent_tree.heading("local", text="本地")
        self.agent_tree.heading("default", text="默认")
        self.agent_tree.heading("actions", text="操作")

        self.agent_tree.column("#0", width=0, stretch=tk.NO)
        self.agent_tree.column("name", width=120)
        self.agent_tree.column("provider", width=80)
        self.agent_tree.column("model", width=120)
        self.agent_tree.column("local", width=50)
        self.agent_tree.column("default", width=50)
        self.agent_tree.column("actions", width=180)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.agent_tree.yview)
        self.agent_tree.configure(yscrollcommand=scrollbar.set)

        self.agent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选择事件和右键菜单
        self.agent_tree.bind("<<TreeviewSelect>>", self.on_agent_select)
        self.agent_tree.bind("<Button-3>", self.show_context_menu)
        self.agent_tree.bind("<Button-1>", self.on_tree_click)

        # 右侧配置面板
        self.config_frame = ttk.LabelFrame(content_frame, text="Agent配置", padding=10)
        self.config_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.config_frame.pack_propagate(False)
        self.config_frame.configure(width=300)

        # 配置面板内容
        self.setup_config_panel()

        # 底部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # 左侧操作按钮
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)

        self.set_default_btn = ttk.Button(
            left_buttons,
            text="设为默认",
            command=self.set_default,
            state=tk.DISABLED
        )
        self.set_default_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_btn = ttk.Button(
            left_buttons,
            text="删除Agent",
            command=self.delete_agent,
            bootstyle=DANGER,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT)

        # 右侧关闭按钮
        ttk.Button(
            button_frame,
            text="关闭",
            command=self.on_close,
            bootstyle=SECONDARY
        ).pack(side=tk.RIGHT)

    def setup_config_panel(self):
        """设置配置面板"""
        # 默认显示提示信息
        self.config_info_label = ttk.Label(
            self.config_frame,
            text="请选择一个Agent查看和编辑配置",
            font=("Microsoft YaHei UI", 10),
            foreground="#666666"
        )
        self.config_info_label.pack(pady=50)

        # 配置变量（用于编辑）
        self.config_name_var = tk.StringVar()
        self.config_provider_var = tk.StringVar()
        self.config_model_var = tk.StringVar()
        self.config_base_url_var = tk.StringVar()
        self.config_api_key_var = tk.StringVar()
        self.config_temp_var = tk.DoubleVar()
        self.config_max_tokens_var = tk.IntVar()
        self.config_system_prompt_var = tk.StringVar()
        self.config_description_var = tk.StringVar()

        # 配置控件（初始隐藏）
        self.config_controls = []
        self.current_agent = None
        self.temp_trace_id = None  # 存储温度trace ID

    def create_config_controls(self):
        """创建配置控件"""
        # 清除现有的trace
        if self.temp_trace_id:
            try:
                self.config_temp_var.trace_vdelete("w", self.temp_trace_id)
            except:
                pass
            self.temp_trace_id = None

        # 清除现有控件
        for widget in self.config_frame.winfo_children():
            widget.destroy()

        # 名称
        ttk.Label(self.config_frame, text="名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(self.config_frame, textvariable=self.config_name_var, width=25)
        name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        self.config_controls.append(name_entry)

        # 提供商
        ttk.Label(self.config_frame, text="提供商:").grid(row=1, column=0, sticky=tk.W, pady=5)
        provider_combo = ttk.Combobox(
            self.config_frame,
            textvariable=self.config_provider_var,
            values=["openai", "ollama", "openrouter", "llamacpp"],
            state="readonly",
            width=22
        )
        provider_combo.grid(row=1, column=1, sticky=tk.EW, pady=5)
        self.config_controls.append(provider_combo)

        # 模型ID
        ttk.Label(self.config_frame, text="模型ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_entry = ttk.Entry(self.config_frame, textvariable=self.config_model_var, width=25)
        model_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)
        self.config_controls.append(model_entry)

        # Base URL
        ttk.Label(self.config_frame, text="Base URL:").grid(row=3, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(self.config_frame, textvariable=self.config_base_url_var, width=25)
        url_entry.grid(row=3, column=1, sticky=tk.EW, pady=5)
        self.config_controls.append(url_entry)

        # API Key
        ttk.Label(self.config_frame, text="API Key:").grid(row=4, column=0, sticky=tk.W, pady=5)
        api_key_entry = ttk.Entry(self.config_frame, textvariable=self.config_api_key_var, width=25, show="*")
        api_key_entry.grid(row=4, column=1, sticky=tk.EW, pady=5)
        self.config_controls.append(api_key_entry)

        # Temperature
        ttk.Label(self.config_frame, text="Temperature:").grid(row=5, column=0, sticky=tk.W, pady=5)
        temp_scale = ttk.Scale(
            self.config_frame,
            from_=0.0,
            to=2.0,
            variable=self.config_temp_var,
            orient=tk.HORIZONTAL,
            length=150
        )
        temp_scale.grid(row=5, column=1, sticky=tk.EW, pady=5)
        self.config_controls.append(temp_scale)

        temp_label = ttk.Label(self.config_frame, text="")
        temp_label.grid(row=5, column=2, padx=(5, 0), pady=5)
        self.config_controls.append(temp_label)

        # 初始化温度显示
        temp_label.configure(text=f"{self.config_temp_var.get():.1f}")

        def update_temp_label(*_):
            try:
                if temp_label and temp_label.winfo_exists():
                    temp_label.configure(text=f"{self.config_temp_var.get():.1f}")
            except (tk.TclError, AttributeError):
                pass

        # 创建新的trace并存储ID
        self.temp_trace_id = self.config_temp_var.trace("w", update_temp_label)

        # Max Tokens
        ttk.Label(self.config_frame, text="Max Tokens:").grid(row=6, column=0, sticky=tk.W, pady=5)
        tokens_entry = ttk.Entry(self.config_frame, textvariable=self.config_max_tokens_var, width=25)
        tokens_entry.grid(row=6, column=1, sticky=tk.EW, pady=5)
        self.config_controls.append(tokens_entry)

        # 系统提示词
        ttk.Label(self.config_frame, text="系统提示词:").grid(row=7, column=0, sticky=tk.NW, pady=5)
        system_text = tk.Text(self.config_frame, height=6, width=25, wrap=tk.WORD)
        system_text.grid(row=7, column=1, columnspan=2, sticky=tk.EW, pady=5)
        self.config_controls.append(system_text)

        def update_system_prompt(*args):
            self.config_system_prompt_var.set(system_text.get("1.0", tk.END).strip())

        system_text.bind("<KeyRelease>", update_system_prompt)
        system_text.bind("<FocusOut>", update_system_prompt)

        # 描述
        ttk.Label(self.config_frame, text="描述:").grid(row=8, column=0, sticky=tk.W, pady=5)
        desc_entry = ttk.Entry(self.config_frame, textvariable=self.config_description_var, width=25)
        desc_entry.grid(row=8, column=1, sticky=tk.EW, pady=5)
        self.config_controls.append(desc_entry)

        # 保存按钮
        save_btn = ttk.Button(
            self.config_frame,
            text="保存修改",
            command=self.save_agent_config,
            bootstyle=SUCCESS
        )
        save_btn.grid(row=9, column=0, columnspan=3, pady=(20, 0))
        self.config_controls.append(save_btn)

        # 配置列权重
        self.config_frame.columnconfigure(1, weight=1)

    def on_tree_click(self, event):
        """处理Treeview点击事件"""
        # 获取点击的位置
        region = self.agent_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        # 获取点击的列和项
        column = self.agent_tree.identify_column(event.x)
        item = self.agent_tree.identify_row(event.y)

        if not item:
            return

        # 如果点击的是操作列（第6列）
        if column == "#6":  # actions列
            # 计算点击位置在操作文本中的区域
            values = self.agent_tree.item(item, "values")
            agent_name = values[0]

            # 获取操作列的宽度和位置
            x_offset = self.agent_tree.bbox(item, column)[0] if self.agent_tree.bbox(item, column) else 0
            relative_x = event.x - x_offset

            # 根据x坐标判断点击的是哪个操作
            # "选择 | 设为默认 | 删除" 大概分为3个区域
            action_width = 180  # actions列的宽度
            if relative_x < action_width / 3:  # 选择区域
                self.select_agent_by_name(agent_name)
            elif relative_x < 2 * action_width / 3:  # 设为默认区域
                self.set_default_agent_by_name(agent_name)
            else:  # 删除区域
                self.delete_agent_by_name(agent_name)

    def select_agent_by_name(self, agent_name):
        """根据名称选择Agent"""
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        for agent in agents:
            if agent.name == agent_name:
                self.chat_app.switch_to_agent(agent.id)
                messagebox.showinfo("成功", f"已选择Agent「{agent_name}」")
                break

    def set_default_agent_by_name(self, agent_name):
        """根据名称设置默认Agent"""
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        for agent in agents:
            if agent.name == agent_name:
                if self.chat_app.agent_manager.set_default_agent(self.chat_app.current_user_id, agent.id):
                    messagebox.showinfo("成功", f"已将「{agent_name}」设为默认Agent")
                    self.load_agents()
                else:
                    messagebox.showerror("错误", "设置默认Agent失败")
                break

    def delete_agent_by_name(self, agent_name):
        """根据名称删除Agent"""
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        target_agent = None
        for agent in agents:
            if agent.name == agent_name:
                target_agent = agent
                break

        if not target_agent:
            return

        # 检查是否是最后一个Agent
        if len(agents) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个Agent")
            return

        # 检查是否是当前Agent
        if target_agent.id == self.chat_app.current_agent_id:
            messagebox.showwarning("警告", "不能删除当前使用的Agent")
            return

        result = messagebox.askyesno(
            "确认删除",
            f"确定要删除Agent「{agent_name}」吗？\n此操作不可撤销！"
        )

        if result:
            if self.chat_app.agent_manager.delete_agent(target_agent.id):
                messagebox.showinfo("成功", "Agent已删除")
                self.load_agents()
                # 如果删除的是当前显示的Agent，隐藏配置面板
                if self.current_agent and self.current_agent.id == target_agent.id:
                    self.hide_config_panel()
                    self.set_default_btn.configure(state=tk.DISABLED)
                    self.delete_btn.configure(state=tk.DISABLED)
            else:
                messagebox.showerror("错误", "删除Agent失败")

    def on_agent_select(self, event):
        """处理Agent选择事件"""
        selection = self.agent_tree.selection()
        if not selection:
            self.hide_config_panel()
            return

        item = selection[0]
        values = self.agent_tree.item(item, "values")
        agent_name = values[0]

        # 找到选中的Agent
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        selected_agent = None
        for agent in agents:
            if agent.name == agent_name:
                selected_agent = agent
                break

        if selected_agent:
            self.show_agent_config(selected_agent)
            # 启用操作按钮
            self.set_default_btn.configure(state=tk.NORMAL)
            self.delete_btn.configure(state=tk.NORMAL)
        else:
            self.hide_config_panel()
            # 禁用操作按钮
            self.set_default_btn.configure(state=tk.DISABLED)
            self.delete_btn.configure(state=tk.DISABLED)

    def show_agent_config(self, agent):
        """显示Agent配置"""
        self.current_agent = agent

        # 创建配置控件
        self.create_config_controls()

        # 加载Agent数据
        self.config_name_var.set(agent.name)
        self.config_provider_var.set(agent.provider)
        self.config_model_var.set(agent.model_id)
        self.config_base_url_var.set(agent.base_url or "")
        self.config_api_key_var.set(agent.api_key or "")
        self.config_temp_var.set(agent.temperature)
        self.config_max_tokens_var.set(agent.max_tokens or 2000)
        self.config_description_var.set(agent.description or "")

        # 设置系统提示词
        for widget in self.config_frame.winfo_children():
            if isinstance(widget, tk.Text) and widget.winfo_height() > 80:
                widget.delete("1.0", tk.END)
                widget.insert("1.0", agent.system_prompt or "")
                break

        self.config_system_prompt_var.set(agent.system_prompt or "")

    def hide_config_panel(self):
        """隐藏配置面板"""
        for widget in self.config_frame.winfo_children():
            widget.destroy()

        self.config_info_label = ttk.Label(
            self.config_frame,
            text="请选择一个Agent查看和编辑配置",
            font=("Microsoft YaHei UI", 10),
            foreground="#666666"
        )
        self.config_info_label.pack(pady=50)
        self.current_agent = None

    def save_agent_config(self):
        """保存Agent配置"""
        if not self.current_agent:
            return

        # 验证输入
        name = self.config_name_var.get().strip()
        if not name:
            messagebox.showerror("错误", "请输入Agent名称")
            return

        model_id = self.config_model_var.get().strip()
        if not model_id:
            messagebox.showerror("错误", "请输入模型ID")
            return

        provider = self.config_provider_var.get()
        if not provider:
            messagebox.showerror("错误", "请选择提供商")
            return

        # 检查名称是否重复
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        for agent in agents:
            if agent.name == name and agent.id != self.current_agent.id:
                messagebox.showerror("错误", "Agent名称已存在")
                return

        # 更新Agent配置
        updated_config = AgentConfig(
            id=self.current_agent.id,
            user_id=self.current_agent.user_id,
            name=name,
            model_id=model_id,
            provider=provider,
            base_url=self.config_base_url_var.get().strip() or None,
            api_key=self.config_api_key_var.get().strip() or None,
            temperature=self.config_temp_var.get(),
            max_tokens=self.config_max_tokens_var.get(),
            system_prompt=self.config_system_prompt_var.get().strip(),
            description=self.config_description_var.get().strip(),
            is_local=provider in ["ollama", "llamacpp"],
            is_default=self.current_agent.is_default
        )

        if self.chat_app.agent_manager.update_agent(self.current_agent.id, updated_config):
            messagebox.showinfo("成功", "Agent配置已更新")
            self.load_agents()  # 刷新列表
            # 重新显示配置
            updated_agent = self.chat_app.agent_manager.get_agent(self.current_agent.id)
            if updated_agent:
                self.show_agent_config(updated_agent)
        else:
            messagebox.showerror("错误", "更新Agent配置失败")

    def load_agents(self):
        """加载Agent列表"""
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)

        # 清空现有项
        for item in self.agent_tree.get_children():
            self.agent_tree.delete(item)

        # 添加Agent
        for agent in agents:
            local_text = "✓" if agent.is_local else ""
            default_text = "✓" if agent.is_default else ""

            # 创建操作按钮文本
            actions_text = "选择 | 设为默认 | 删除"

            item = self.agent_tree.insert(
                "",
                tk.END,
                values=(
                    agent.name,
                    agent.provider,
                    agent.model_id,
                    local_text,
                    default_text,
                    actions_text
                )
            )

        # 绑定列点击事件
        self.agent_tree.bind("<Button-1>", self.on_tree_click)

    def show_context_menu(self, event):
        """显示右键菜单"""
        selection = self.agent_tree.selection()
        if not selection:
            return

        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="编辑", command=self.edit_agent)
        context_menu.add_command(label="设为默认", command=self.set_default)
        context_menu.add_separator()
        context_menu.add_command(label="删除", command=self.delete_agent)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def create_agent(self):
        """创建Agent"""
        dialog = AgentEditDialog(self, self.chat_app, title="新建Agent")
        self.wait_window(dialog)

        if dialog.result:
            self.load_agents()

    def edit_agent(self):
        """编辑Agent"""
        selection = self.agent_tree.selection()
        if not selection:
            return

        # 触发选择事件来显示配置面板
        self.on_agent_select(None)

    def set_default(self):
        """设为默认"""
        if not self.current_agent:
            return

        if self.chat_app.agent_manager.set_default_agent(self.chat_app.current_user_id, self.current_agent.id):
            messagebox.showinfo("成功", f"已将「{self.current_agent.name}」设为默认Agent")
            self.load_agents()
            # 重新加载配置
            updated_agent = self.chat_app.agent_manager.get_agent(self.current_agent.id)
            if updated_agent:
                self.show_agent_config(updated_agent)
        else:
            messagebox.showerror("错误", "设置默认Agent失败")

    def delete_agent(self):
        """删除Agent"""
        if not self.current_agent:
            return

        # 检查是否是最后一个Agent
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        if len(agents) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个Agent")
            return

        # 检查是否是当前Agent
        if self.current_agent.id == self.chat_app.current_agent_id:
            messagebox.showwarning("警告", "不能删除当前使用的Agent")
            return

        result = messagebox.askyesno(
            "确认删除",
            f"确定要删除Agent「{self.current_agent.name}」吗？\n此操作不可撤销！"
        )

        if result:
            if self.chat_app.agent_manager.delete_agent(self.current_agent.id):
                messagebox.showinfo("成功", "Agent已删除")
                self.load_agents()
                # 隐藏配置面板
                self.hide_config_panel()
                # 禁用操作按钮
                self.set_default_btn.configure(state=tk.DISABLED)
                self.delete_btn.configure(state=tk.DISABLED)
            else:
                messagebox.showerror("错误", "删除Agent失败")

    def on_close(self):
        """关闭"""
        # 清理trace
        if self.temp_trace_id:
            try:
                self.config_temp_var.trace_vdelete("w", self.temp_trace_id)
            except:
                pass
        self.destroy()


class AgentEditDialog(ttb.Toplevel):
    """Agent编辑对话框"""

    def __init__(self, parent, chat_app, agent=None, title=None, **kwargs):
        # 移除title从kwargs，避免重复传递
        if 'title' in kwargs:
            del kwargs['title']
        super().__init__(parent, **kwargs)
        self.chat_app = chat_app
        self.agent = agent
        self.result = None

        self.title(title or "编辑Agent")
        self.geometry("500x600")
        self.resizable(True, True)

        # 居中显示
        self.center_window()
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        if agent:
            self.load_agent_data()

        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        """设置UI"""
        # 主框架
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 滚动框架
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 表单字段
        row = 0

        # 名称
        ttk.Label(scrollable_frame, text="Agent名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.name_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # 提供商
        ttk.Label(scrollable_frame, text="提供商:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.provider_var = tk.StringVar()
        provider_combo = ttk.Combobox(
            scrollable_frame,
            textvariable=self.provider_var,
            values=["openai", "ollama", "openrouter", "llamacpp"],
            state="readonly",
            width=37
        )
        provider_combo.grid(row=row, column=1, sticky=tk.EW, pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)
        row += 1

        # 模型ID
        ttk.Label(scrollable_frame, text="模型ID:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.model_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Base URL
        ttk.Label(scrollable_frame, text="Base URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.base_url_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # API Key
        ttk.Label(scrollable_frame, text="API Key:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.api_key_var, width=40, show="*").grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Temperature
        ttk.Label(scrollable_frame, text="Temperature:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.7)
        temp_frame = ttk.Frame(scrollable_frame)
        temp_frame.grid(row=row, column=1, sticky=tk.EW, pady=5)

        self.temp_scale = ttk.Scale(
            temp_frame,
            from_=0.0,
            to=2.0,
            variable=self.temperature_var,
            orient=tk.HORIZONTAL
        )
        self.temp_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.temp_label = ttk.Label(temp_frame, text="0.7")
        self.temp_label.pack(side=tk.RIGHT, padx=(10, 0))

        self.temperature_var.trace("w", self.update_temp_label)
        row += 1

        # Max Tokens
        ttk.Label(scrollable_frame, text="Max Tokens:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=2000)
        ttk.Entry(scrollable_frame, textvariable=self.max_tokens_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # 系统提示词
        ttk.Label(scrollable_frame, text="系统提示词:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.system_prompt_var = tk.StringVar(value="你是一个有用的AI助手，请用简洁明了的语言回答问题。")
        system_prompt_text = tk.Text(scrollable_frame, height=8, width=40, wrap=tk.WORD)
        system_prompt_text.grid(row=row, column=1, sticky=tk.EW, pady=5)

        # 设置默认文本
        system_prompt_text.insert("1.0", self.system_prompt_var.get())

        def update_system_prompt(*args):
            self.system_prompt_var.set(system_prompt_text.get("1.0", tk.END).strip())

        system_prompt_text.bind("<KeyRelease>", update_system_prompt)
        system_prompt_text.bind("<FocusOut>", update_system_prompt)
        row += 1

        # 描述
        ttk.Label(scrollable_frame, text="描述:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.description_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # 设为默认
        self.is_default_var = tk.BooleanVar()
        ttk.Checkbutton(
            scrollable_frame,
            text="设为默认Agent",
            variable=self.is_default_var
        ).grid(row=row, column=1, sticky=tk.W, pady=10)

        # 配置列权重
        scrollable_frame.columnconfigure(1, weight=1)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="取消",
            command=self.on_cancel,
            bootstyle=SECONDARY
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            button_frame,
            text="保存",
            command=self.on_save,
            bootstyle=SUCCESS
        ).pack(side=tk.RIGHT)

    def update_temp_label(self, *args):
        """更新温度标签"""
        self.temp_label.configure(text=f"{self.temperature_var.get():.1f}")

    def on_provider_change(self, event):
        """提供商改变时的处理"""
        provider = self.provider_var.get()

        # 根据提供商设置默认值
        if provider == "openai":
            self.base_url_var.set("https://api.openai.com/v1")
            self.model_var.set("gpt-4o-mini")
        elif provider == "ollama":
            self.base_url_var.set("http://localhost:11434")
            self.model_var.set("llama3.2:latest")
        elif provider == "openrouter":
            self.base_url_var.set("https://openrouter.ai/api/v1")
            self.model_var.set("meta-llama/llama-3.2-3b-instruct:free")
        elif provider == "llamacpp":
            self.base_url_var.set("http://127.0.0.1:8080/v1")
            self.model_var.set("local-model")

    def load_agent_data(self):
        """加载Agent数据"""
        if self.agent:
            self.name_var.set(self.agent.name)
            self.provider_var.set(self.agent.provider)
            self.model_var.set(self.agent.model_id)
            self.base_url_var.set(self.agent.base_url or "")
            self.api_key_var.set(self.agent.api_key or "")
            self.temperature_var.set(self.agent.temperature)
            self.max_tokens_var.set(self.agent.max_tokens or 2000)
            self.system_prompt_var.set(self.agent.system_prompt)
            self.description_var.set(self.agent.description)
            self.is_default_var.set(self.agent.is_default)

            # 更新系统提示词文本框
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Canvas):
                            for item in child.winfo_children():
                                if isinstance(item, ttk.Frame):
                                    for subitem in item.winfo_children():
                                        if isinstance(subitem, tk.Text) and subitem.winfo_height() > 100:
                                            subitem.delete("1.0", tk.END)
                                            subitem.insert("1.0", self.agent.system_prompt)
                                            break

    def on_save(self):
        """保存"""
        # 验证输入
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("错误", "请输入Agent名称")
            return

        model_id = self.model_var.get().strip()
        if not model_id:
            messagebox.showerror("错误", "请输入模型ID")
            return

        provider = self.provider_var.get()
        if not provider:
            messagebox.showerror("错误", "请选择提供商")
            return

        # 检查名称是否重复
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        for agent in agents:
            if agent.name == name and (not self.agent or agent.id != self.agent.id):
                messagebox.showerror("错误", "Agent名称已存在")
                return

        # 创建或更新Agent配置
        if self.agent:
            # 更新现有Agent
            updated_config = AgentConfig(
                id=self.agent.id,
                user_id=self.agent.user_id,
                name=name,
                model_id=model_id,
                provider=provider,
                base_url=self.base_url_var.get().strip() or None,
                api_key=self.api_key_var.get().strip() or None,
                temperature=self.temperature_var.get(),
                max_tokens=self.max_tokens_var.get(),
                system_prompt=self.system_prompt_var.get().strip(),
                description=self.description_var.get().strip(),
                is_local=provider in ["ollama", "llamacpp"],
                is_default=self.is_default_var.get()
            )

            if self.chat_app.agent_manager.update_agent(self.agent.id, updated_config):
                messagebox.showinfo("成功", "Agent已更新")
                self.result = True
                self.destroy()
            else:
                messagebox.showerror("错误", "更新Agent失败")
        else:
            # 创建新Agent
            new_config = AgentConfig(
                user_id=self.chat_app.current_user_id,
                name=name,
                model_id=model_id,
                provider=provider,
                base_url=self.base_url_var.get().strip() or None,
                api_key=self.api_key_var.get().strip() or None,
                temperature=self.temperature_var.get(),
                max_tokens=self.max_tokens_var.get(),
                system_prompt=self.system_prompt_var.get().strip(),
                description=self.description_var.get().strip(),
                is_local=provider in ["ollama", "llamacpp"],
                is_default=self.is_default_var.get()
            )

            try:
                new_agent = self.chat_app.agent_manager.create_agent(
                    self.chat_app.current_user_id,
                    new_config
                )
                messagebox.showinfo("成功", "Agent已创建")
                self.result = True
                self.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"创建Agent失败: {str(e)}")

    def on_cancel(self):
        """取消"""
        self.result = None
        self.destroy()


class SessionDialog(ttb.Toplevel):
    """会话对话框"""

    def __init__(self, parent, chat_app, **kwargs):
        super().__init__(parent, **kwargs)
        self.chat_app = chat_app
        self.result = None

        self.title(kwargs.get("title", "会话设置"))
        self.geometry("400x300")
        self.resizable(True, True)

        # 居中显示
        self.center_window()
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = 400  # 固定宽度
        height = 300  # 固定高度
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        """设置UI"""
        # 主框架
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # 会话标题
        ttk.Label(main_frame, text="会话标题:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.title_var, width=30).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # 会话描述
        ttk.Label(main_frame, text="会话描述:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.description_var, width=30).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # 选择Agent
        ttk.Label(main_frame, text="选择Agent:").grid(row=row, column=0, sticky=tk.W, pady=5)
        agent_frame = ttk.Frame(main_frame)
        agent_frame.grid(row=row, column=1, sticky=tk.EW, pady=5)

        self.agent_var = tk.StringVar()
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        if agents:
            # 默认选择默认Agent
            default_agent = None
            for agent in agents:
                if agent.is_default:
                    default_agent = agent
                    break

            selected_agent = default_agent or agents[0]
            self.agent_var.set(selected_agent.name)

        self.agent_combo = ttk.Combobox(
            agent_frame,
            textvariable=self.agent_var,
            values=[agent.name for agent in agents],
            state="readonly",
            width=25
        )
        self.agent_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        row += 1

        # 配置列权重
        main_frame.columnconfigure(1, weight=1)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="取消",
            command=self.on_cancel,
            bootstyle=SECONDARY
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            button_frame,
            text="确定",
            command=self.on_confirm,
            bootstyle=SUCCESS
        ).pack(side=tk.RIGHT)

    def on_confirm(self):
        """确认"""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("错误", "请输入会话标题")
            return

        # 检查标题是否重复
        sessions = self.chat_app.session_manager.get_user_sessions(self.chat_app.current_user_id)
        for session in sessions:
            if session.title == title:
                messagebox.showerror("错误", "会话标题已存在")
                return

        # 找到选择的Agent
        agents = self.chat_app.agent_manager.get_user_agents(self.chat_app.current_user_id)
        selected_agent = None
        for agent in agents:
            if agent.name == self.agent_var.get():
                selected_agent = agent
                break

        if not selected_agent:
            messagebox.showerror("错误", "请选择一个Agent")
            return

        try:
            new_session = self.chat_app.session_manager.create_session(
                self.chat_app.current_user_id,
                title,
                self.description_var.get().strip() or None,
                selected_agent.id
            )

            self.result = {
                'session_id': new_session.id,
                'agent_id': selected_agent.id
            }

            self.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"创建会话失败: {str(e)}")

    def on_cancel(self):
        """取消"""
        self.result = None
        self.destroy()


class ChatAppGUI:
    """聊天应用GUI主类"""

    def __init__(self):
        self.root = ttb.Window(themename="yeti")
        self.root.title("AI聊天客户端")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # 初始化数据库和管理器
        self.db_manager = DatabaseManager(DatabaseType.SQLITE, "autobox_id.db")
        self.user_manager = UserManager(self.db_manager)
        self.agent_manager = AgentManager(self.db_manager)
        self.session_manager = SessionManager(self.db_manager)
        self.conversation_manager = ConversationManager(self.db_manager)

        # 初始化默认数据
        self._init_default_data()

        # 设置UI
        self.setup_ui()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _init_default_data(self):
        """初始化默认数据"""
        # 创建默认用户（如果不存在）
        default_user = self.user_manager.get_user_by_username("default")
        if not default_user:
            default_user = self.user_manager.create_user("default", "default@autobox.com")

        self.current_user_id = default_user.id

        # 创建默认Agent（如果不存在）
        default_agents = self.agent_manager.get_user_agents(default_user.id)
        if not default_agents:
            # OpenAI GPT-4o-mini
            openai_config = AgentConfig(
                user_id=default_user.id,
                name="OpenAI GPT-4o-mini",
                model_id="gpt-4o-mini",
                provider="openai",
                base_url="https://api.openai.com/v1",
                api_key="sk-3KdzUkc4E8wKKx7NnioVwV8R485m7EDqmL3IFBiD4UUOvlwr",  # 默认API密钥
                description="OpenAI的GPT-4o mini模型，适合一般对话",
                is_default=True
            )
            self.agent_manager.create_agent(default_user.id, openai_config)

            # Ollama 模型（如果可用）
            if OLLAMA_AVAILABLE:
                ollama_config = AgentConfig(
                    user_id=default_user.id,
                    name="Ollama Default",
                    model_id="llama3.2:latest",
                    provider="ollama",
                    base_url="http://localhost:11434",
                    is_local=True,
                    description="本地Ollama模型"
                )
                self.agent_manager.create_agent(default_user.id, ollama_config)

        # 设置当前Agent
        current_agent = self.agent_manager.get_user_default_agent(default_user.id)
        if current_agent:
            self.current_agent_id = current_agent.id
        else:
            agents = self.agent_manager.get_user_agents(default_user.id)
            if agents:
                self.current_agent_id = agents[0].id
            else:
                self.current_agent_id = None

        # 创建默认会话（如果不存在）
        user_sessions = self.session_manager.get_user_sessions(default_user.id)
        if not user_sessions:
            default_session = self.session_manager.create_session(
                default_user.id,
                "默认会话",
                "默认的对话会话",
                self.current_agent_id
            )
            self.current_session_id = default_session.id
        else:
            self.current_session_id = user_sessions[0].id
            # 更新会话的当前Agent
            if self.current_agent_id:
                self.session_manager.update_session(self.current_session_id, current_agent_id=self.current_agent_id)

    def setup_ui(self):
        """设置UI"""
        # 创建主容器
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 左侧边栏（会话列表）
        left_frame = ttk.Frame(main_container, width=250)
        main_container.add(left_frame, weight=1)

        # 会话列表
        self.session_list = SessionListFrame(left_frame, self)
        self.session_list.pack(fill=tk.BOTH, expand=True)

        # 右侧聊天区域
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=3)

        # 聊天显示区域（75%高度）
        self.chat_display = ChatDisplayFrame(right_frame, self)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 输入区域（25%高度）
        input_container = ttk.Frame(right_frame)
        input_container.pack(fill=tk.X, side=tk.BOTTOM)

        # 分隔线
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, side=tk.BOTTOM)

        # 输入框架
        self.input_frame = InputFrame(input_container, self)
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def switch_to_session(self, session_id: str):
        """切换到指定会话"""
        if session_id == self.current_session_id:
            return

        self.current_session_id = session_id

        # 更新会话的Agent
        session = self.session_manager.get_session(session_id)
        if session and session.current_agent_id:
            self.current_agent_id = session.current_agent_id
            self.input_frame.update_agent_button_text()

        # 刷新聊天显示
        self.refresh_chat_display()

        # 刷新会话列表
        self.session_list.refresh_session_list()

    def switch_to_agent(self, agent_id: str):
        """切换到指定Agent"""
        self.current_agent_id = agent_id

        # 更新当前会话的Agent
        if self.current_session_id:
            self.session_manager.update_session(self.current_session_id, current_agent_id=agent_id)

        self.input_frame.update_agent_button_text()

    def refresh_chat_display(self):
        """刷新聊天显示"""
        self.chat_display.refresh_display()

    def create_agent_instance(self, config: AgentConfig):
        """根据配置创建模型实例"""
        try:
            if config.provider == "openai":
                if not OPENAI_AVAILABLE:
                    raise ImportError("OpenAI库未安装")

                if not config.api_key or config.api_key == "your_api_key_here":
                    print(f"[错误] OpenAI API密钥未设置或使用默认值")
                    return None

                return OpenAIChat(
                    id=config.model_id,
                    api_key=config.api_key,
                    base_url=config.base_url,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )

            elif config.provider == "ollama":
                if not OLLAMA_AVAILABLE:
                    raise ImportError("Ollama库未安装")

                options = {
                    "temperature": config.temperature,
                }
                if config.max_tokens:
                    options["num_predict"] = config.max_tokens

                return Ollama(
                    id=config.model_id,
                    host=config.base_url,
                    options=options,
                )

            elif config.provider == "openrouter":
                if not OPENROUTER_AVAILABLE:
                    raise ImportError("OpenRouter支持不可用")

                return OpenRouter(
                    id=config.model_id,
                    api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    base_url=config.base_url,
                )

            elif config.provider == "llamacpp":
                if not LLAMACPP_AVAILABLE:
                    raise ImportError("llama.cpp支持不可用")

                return LlamaCpp(
                    id=config.model_id,
                    api_key=config.api_key or "not-required",
                    base_url=config.base_url,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )

            else:
                raise ValueError(f"不支持的提供商: {config.provider}")

        except Exception as e:
            print(f"[错误] 创建模型实例失败: {str(e)}")
            return None

    def get_current_agent(self):
        """获取当前Agent实例"""
        if not self.current_agent_id:
            return None

        agent_config = self.agent_manager.get_agent(self.current_agent_id)
        if not agent_config:
            return None

        return self.create_agent_instance(agent_config)

    def chat_streaming(self, user_prompt: str):
        """流式聊天"""
        agent = self.get_current_agent()
        if not agent:
            yield "[错误] 没有可用的Agent"
            return

        # 使用配置版本的流式聊天
        for chunk in self.chat_streaming_with_config(user_prompt, agent):
            yield chunk

    def chat_streaming_with_config(self, user_prompt: str, agent_config):
        """使用预设Agent配置的流式聊天，避免在后台线程中访问数据库"""
        print(f"[调试] 开始流式聊天: {user_prompt[:50]}...")
        print(f"[调试] Agent配置: {agent_config.provider}, {agent_config.model_id}")

        try:
            agent_instance = self.create_agent_instance(agent_config)
            if not agent_instance:
                print("[调试] 创建模型实例失败")
                yield "[错误] 创建模型实例失败"
                return

            # 获取系统提示词
            system_prompt = getattr(agent_config, 'system_prompt', '你是一个有用的AI助手。')
            print(f"[调试] 系统提示词: {system_prompt[:50]}...")

            agent_obj = Agent(
                model=agent_instance,
                instructions=[system_prompt],
                markdown=True,
            )
            print(f"[调试] Agent对象创建成功，开始运行")

            chunk_count = 0
            for chunk in agent_obj.run(user_prompt, stream=True):
                if hasattr(chunk, 'content') and chunk.content:
                    chunk_count += 1
                    print(f"[调试] 生成chunk {chunk_count}: {chunk.content[:30]}...")
                    yield chunk.content
                elif hasattr(chunk, 'text') and chunk.text:
                    chunk_count += 1
                    print(f"[调试] 生成chunk {chunk_count}: {chunk.text[:30]}...")
                    yield chunk.text

            print(f"[调试] 流式聊天完成，总共生成{chunk_count}个chunk")

        except Exception as e:
            print(f"[调试] 流式聊天异常: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"[错误] 流式聊天失败: {str(e)}"

    def on_closing(self):
        """关闭应用"""
        if messagebox.askokcancel("退出", "确定要退出AI聊天客户端吗？"):
            self.db_manager.close()
            self.root.destroy()

    def run(self):
        """运行应用"""
        self.root.mainloop()




def main():
    """主函数"""
    if not TTKBOOTSTRAP_AVAILABLE:
        messagebox.showerror("依赖缺失", "ttkbootstrap库未安装\n\n请运行以下命令安装：\npip install ttkbootstrap\n\n然后重新启动程序")
        return

    try:
        app = ChatAppGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("启动错误", f"应用启动失败: {str(e)}")


if __name__ == "__main__":
    main()