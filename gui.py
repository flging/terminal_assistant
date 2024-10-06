import tkinter as tk
from tkinter import ttk, font

class BubbleChat(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.messages = []
        self.font = font.Font(family="Arial", size=10)

    def add_message(self, text, sender):
        self.messages.append((text, sender))
        self.redraw()

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=20, **kwargs):
        points = [x1+radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def redraw(self):
        self.delete("all")
        width = self.winfo_width()
        y = 10
        for text, sender in self.messages:
            if sender == "user":
                fill = "#DCF8C6"
                text_fill = "black"
            else:
                fill = "#E5E5EA"
                text_fill = "black"

            lines = text.split('\n')
            max_width = min(400, width - 100)
            wrapped_lines = []
            for line in lines:
                if self.font.measure(line) > max_width:
                    current_line = ""
                    for word in line.split():
                        if self.font.measure(current_line + word) <= max_width:
                            current_line += word + " "
                        else:
                            wrapped_lines.append(current_line)
                            current_line = word + " "
                    if current_line:
                        wrapped_lines.append(current_line)
                else:
                    wrapped_lines.append(line)

            text_width = max(self.font.measure(line) for line in wrapped_lines)
            bubble_width = text_width + 40
            line_height = self.font.metrics("linespace")
            text_height = len(wrapped_lines) * line_height
            bubble_height = text_height + 20

            if sender == "user":
                bubble_x = width - bubble_width - 10
            else:
                bubble_x = 10

            self.create_rounded_rectangle(bubble_x, y, bubble_x+bubble_width, y+bubble_height, fill=fill, outline="")

            text_y = y + (bubble_height - text_height) // 2
            for line in wrapped_lines:
                if sender == "user":
                    text_x = bubble_x + bubble_width - 20
                    anchor = "e"
                else:
                    text_x = bubble_x + 20
                    anchor = "w"
                
                self.create_text(text_x,
                                 text_y + line_height // 2,
                                 text=line,
                                 anchor=anchor,
                                 fill=text_fill,
                                 font=self.font)
                text_y += line_height

            y += bubble_height + 10

        self.config(scrollregion=self.bbox("all"))

class ScrollableBubbleChat(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = BubbleChat(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.bind('<Enter>', self._bind_mouse_scroll)
        self.canvas.bind('<Leave>', self._unbind_mouse_scroll)

        self.scrollbar.pack(side="right", fill="y")

    def _bind_mouse_scroll(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_scroll)

    def _unbind_mouse_scroll(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mouse_scroll(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_message(self, text, sender):
        self.canvas.add_message(text, sender)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(1)