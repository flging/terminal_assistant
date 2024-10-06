import tkinter as tk
from tkinter import ttk, messagebox
from gui import ScrollableBubbleChat
from terminal_assistant import TerminalAssistant
import threading

class TerminalAssistantGUI:
    def __init__(self, master):
        self.master = master
        master.title("Terminal Assistant")
        master.geometry("1000x800")

        self.assistant = TerminalAssistant()
        self.use_rag = tk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        api_frame = ttk.Frame(self.master)
        api_frame.pack(pady=10)
        ttk.Label(api_frame, text="API Key:").pack(side=tk.LEFT)
        self.api_entry = ttk.Entry(api_frame, width=50, show="*")
        self.api_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(api_frame, text="Set API Key", command=self.set_api_key).pack(side=tk.LEFT)

        main_frame = ttk.Frame(self.master)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(chat_frame, text="Chat").pack()
        self.chat_display = ScrollableBubbleChat(chat_frame)
        self.chat_display.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        command_frame = ttk.Frame(main_frame)
        command_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(command_frame, text="Command Execution Results").pack()
        self.command_display = tk.Text(command_frame, height=30, state='disabled')
        self.command_display.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.master)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.user_input = ttk.Entry(control_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = ttk.Button(control_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        rag_frame = ttk.Frame(self.master)
        rag_frame.pack(pady=5)
        ttk.Checkbutton(rag_frame, text="Use RAG", variable=self.use_rag).pack()

    def set_api_key(self):
        api_key = self.api_entry.get()
        self.assistant.set_api_key(api_key)
        result = self.assistant.load_RAG_DB()
        self.update_chat(result, "assistant")

    def update_chat(self, message, sender):
        self.chat_display.add_message(message, sender)

    def update_command(self, message, message_type):
        self.command_display.configure(state='normal')
        if message_type == "input":
            self.command_display.insert(tk.END, f"$ {message}\n", "command_input")
        elif message_type == "output":
            self.command_display.insert(tk.END, f"{message.strip()}\n", "command_output")
            self.command_display.insert(tk.END, "-"*50 + "\n", "command_separator")
        self.command_display.see(tk.END)
        self.command_display.configure(state='disabled')

    def send_message(self, event=None):
        user_message = self.user_input.get()
        if not user_message.strip():
            return
        self.user_input.delete(0, tk.END)
        self.update_chat(user_message, "user")
        
        self.send_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        threading.Thread(target=self.process_message, args=(user_message,)).start()

    def process_message(self, user_message):
        responses = self.assistant.process_message(user_message, use_rag=self.use_rag.get())
        for response_type, content in responses:
            if response_type == "assistant":
                self.update_chat(content, "assistant")
            elif response_type == "command_input":
                self.update_command(content, "input")
            elif response_type == "command_output":
                self.update_command(content, "output")
            elif response_type == "rag_result":
                self.update_chat(f"RAG Search Results: {content}", "assistant")
            elif response_type == "error":
                self.update_chat(f"Error: {content}", "assistant")
        
        self.send_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def stop_processing(self):
        result = self.assistant.stop_processing()
        self.update_chat(result, "assistant")

def main():
    root = tk.Tk()
    app = TerminalAssistantGUI(root)
    
    app.command_display.tag_configure("command_input", foreground="sky blue")
    app.command_display.tag_configure("command_output", foreground="white")
    app.command_display.tag_configure("command_separator", foreground="gray")
    
    root.mainloop()

if __name__ == "__main__":
    main()