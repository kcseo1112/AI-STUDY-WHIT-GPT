# TCP_file_GUI_server.py
# TCP File Transfer GUI Server
import socket
import os
import sys
import platform
import threading
from tkinter import *
from tkinter import scrolledtext, messagebox, ttk

HOST = ''  # Use '' or '0.0.0.0' to listen on all interfaces
PORT = 2501
BUFSIZE = 4096  # Buffer size for file transfer (4KB)
RECEIVE_DIR = "received_files"  # Directory to save received files

# Font settings for cross-platform compatibility
if sys.platform == 'linux':
    DEFAULT_FONT = ("DejaVu Sans", 10)
    DEFAULT_FONT_BOLD = ("DejaVu Sans", 10, "bold")
    MONOSPACE_FONT = ("DejaVu Sans Mono", 9)
    # Force UTF-8 encoding
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
else:
    # Windows font settings
    DEFAULT_FONT = ("Arial", 10)
    DEFAULT_FONT_BOLD = ("Arial", 10, "bold")
    MONOSPACE_FONT = ("Consolas", 9)

class TCPFileServer:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP File Transfer Server")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        self.server_socket = None
        self.is_running = False
        self.server_thread = None
        self.received_files = []  # List of received files
        
        self.create_widgets()
        self.ensure_receive_directory()
        self.refresh_file_list()
        
    def create_widgets(self):
        # Top frame: Server settings
        top_frame = Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=X)
        
        Label(top_frame, text="Server Address:", font=DEFAULT_FONT).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.host_entry = Entry(top_frame, width=20, font=DEFAULT_FONT)
        self.host_entry.insert(0, HOST)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        
        Label(top_frame, text="Port:", font=DEFAULT_FONT).grid(row=0, column=2, sticky=W, padx=5, pady=5)
        self.port_entry = Entry(top_frame, width=10, font=DEFAULT_FONT)
        self.port_entry.insert(0, str(PORT))
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        
        self.start_btn = Button(top_frame, text="Start Server", command=self.start_server,
                               bg="#4CAF50", fg="white", font=DEFAULT_FONT_BOLD,
                               width=12)
        self.start_btn.grid(row=0, column=4, padx=5, pady=5)
        
        self.stop_btn = Button(top_frame, text="Stop Server", command=self.stop_server,
                               bg="#f44336", fg="white", font=DEFAULT_FONT_BOLD,
                               width=12, state=DISABLED)
        self.stop_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # Server status display
        self.status_label = Label(top_frame, text="Server Stopped", fg="red", font=DEFAULT_FONT)
        self.status_label.grid(row=1, column=0, columnspan=6, sticky=W, padx=5, pady=2)
        
        # Save path display
        path_label = Label(top_frame, text=f"Receive Directory: {os.path.abspath(RECEIVE_DIR)}",
                          font=DEFAULT_FONT, fg="gray")
        path_label.grid(row=2, column=0, columnspan=6, sticky=W, padx=5, pady=2)
        
        # Middle frame: Current connection info and progress
        mid_frame = Frame(self.root, padx=10, pady=10)
        mid_frame.pack(fill=X)
        
        Label(mid_frame, text="Current Connection:", font=DEFAULT_FONT_BOLD).pack(anchor=W)
        self.connection_label = Label(mid_frame, text="No Connection", font=DEFAULT_FONT, fg="gray")
        self.connection_label.pack(anchor=W, pady=2)
        
        # Progress display
        self.progress_label = Label(mid_frame, text="", font=DEFAULT_FONT)
        self.progress_label.pack(fill=X, pady=5)
        
        self.progress_bar = Label(mid_frame, text="", bg="#e0e0e0", height=2, anchor=W)
        self.progress_bar.pack(fill=X, pady=2)
        
        # Main container: File list and log side by side
        main_container = Frame(self.root)
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Left frame: Received files list and content preview
        left_frame = Frame(main_container)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        Label(left_frame, text="Received Files:", font=DEFAULT_FONT_BOLD).pack(anchor=W, pady=(0, 5))
        
        # File list and refresh button
        list_btn_frame = Frame(left_frame)
        list_btn_frame.pack(fill=X, pady=(0, 5))
        
        self.refresh_btn = Button(list_btn_frame, text="Refresh", command=self.refresh_file_list,
                                  font=DEFAULT_FONT, width=10)
        self.refresh_btn.pack(side=LEFT, padx=(0, 5))
        
        self.view_btn = Button(list_btn_frame, text="View File", command=self.view_selected_file,
                               font=DEFAULT_FONT, width=10, state=DISABLED)
        self.view_btn.pack(side=LEFT)
        
        # File list
        list_frame = Frame(left_frame)
        list_frame.pack(fill=BOTH, expand=True)
        
        scrollbar_list = Scrollbar(list_frame)
        scrollbar_list.pack(side=RIGHT, fill=Y)
        
        self.file_listbox = Listbox(list_frame, font=DEFAULT_FONT, yscrollcommand=scrollbar_list.set)
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        scrollbar_list.config(command=self.file_listbox.yview)
        
        # File content preview
        Label(left_frame, text="File Content Preview:", font=DEFAULT_FONT_BOLD).pack(anchor=W, pady=(10, 5))
        
        self.file_content_text = scrolledtext.ScrolledText(left_frame, height=15, width=40,
                                                           font=MONOSPACE_FONT, wrap=WORD)
        self.file_content_text.pack(fill=BOTH, expand=True)
        
        # Right frame: Log output
        right_frame = Frame(main_container)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 0))
        
        Label(right_frame, text="Server Log:", font=DEFAULT_FONT_BOLD).pack(anchor=W)
        
        self.log_text = scrolledtext.ScrolledText(right_frame, height=30, width=50,
                                                   font=MONOSPACE_FONT, wrap=WORD)
        self.log_text.pack(fill=BOTH, expand=True, pady=5)
        
    def log(self, message):
        """Add log message (UTF-8 encoding guaranteed)"""
        try:
            if isinstance(message, bytes):
                message = message.decode('utf-8', errors='replace')
            elif not isinstance(message, str):
                message = str(message)
            # Safely handle UTF-8 encoded strings
            self.log_text.insert(END, message + "\n")
            self.log_text.see(END)
            self.root.update()
        except Exception as e:
            # Continue execution even if log output fails
            print(f"Log output error: {e}", file=sys.stderr)
        
    def ensure_receive_directory(self):
        """Create receive directory if it doesn't exist"""
        if not os.path.exists(RECEIVE_DIR):
            os.makedirs(RECEIVE_DIR)
            self.log(f"Directory created: {RECEIVE_DIR}")
    
    def refresh_file_list(self):
        """Refresh received files list"""
        self.file_listbox.delete(0, END)
        self.received_files = []
        
        if os.path.exists(RECEIVE_DIR):
            try:
                files = sorted(os.listdir(RECEIVE_DIR), key=lambda x: os.path.getmtime(os.path.join(RECEIVE_DIR, x)), reverse=True)
                for filename in files:
                    file_path = os.path.join(RECEIVE_DIR, filename)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        size_str = self.format_file_size(file_size)
                        display_name = f"{filename} ({size_str})"
                        self.file_listbox.insert(END, display_name)
                        self.received_files.append(file_path)
            except Exception as e:
                self.log(f"Error refreshing file list: {e}")
    
    def format_file_size(self, size):
        """Convert file size to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def on_file_select(self, event):
        """When file is selected from list"""
        selection = self.file_listbox.curselection()
        if selection:
            self.view_btn.config(state=NORMAL)
            # Preview selected file content
            file_index = selection[0]
            if file_index < len(self.received_files):
                self.preview_file(self.received_files[file_index])
        else:
            self.view_btn.config(state=DISABLED)
    
    def preview_file(self, file_path):
        """Preview file content"""
        self.file_content_text.delete(1.0, END)
        
        try:
            if not os.path.exists(file_path):
                self.file_content_text.insert(END, "File not found.")
                return
            
            file_size = os.path.getsize(file_path)
            
            # Limit preview size for large files
            max_preview_size = 100 * 1024  # 100KB
            if file_size > max_preview_size:
                self.file_content_text.insert(END, f"File is too large ({self.format_file_size(file_size)}).\n")
                self.file_content_text.insert(END, f"Showing first {self.format_file_size(max_preview_size)} only.\n\n")
                preview_size = max_preview_size
            else:
                preview_size = file_size
            
            # Check if file is text file (simple heuristic)
            is_text_file = self.is_text_file(file_path)
            
            if is_text_file:
                # Text file: try multiple encodings
                encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
                content_read = False
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                            content = f.read(preview_size)
                            self.file_content_text.insert(END, content)
                            content_read = True
                            break
                    except:
                        continue
                
                if not content_read:
                    # If all encodings fail, show as binary
                    with open(file_path, 'rb') as f:
                        data = f.read(preview_size)
                        self.file_content_text.insert(END, f"[Binary File]\n\n")
                        self.file_content_text.insert(END, data.hex()[:2000])  # First 2000 chars only
            else:
                # Binary file: show as hexadecimal
                with open(file_path, 'rb') as f:
                    data = f.read(preview_size)
                    self.file_content_text.insert(END, f"[Binary File - Hexadecimal]\n\n")
                    # Convert to hex and display (max 2000 bytes)
                    hex_str = data[:2000].hex()
                    # Format for readability
                    formatted_hex = ' '.join(hex_str[i:i+2] for i in range(0, min(len(hex_str), 2000), 2))
                    self.file_content_text.insert(END, formatted_hex)
                    if len(data) > 2000:
                        self.file_content_text.insert(END, f"\n\n... (Total {file_size} bytes, showing first 2000 bytes only)")
                        
        except Exception as e:
            self.file_content_text.insert(END, f"File read error: {e}")
    
    def is_text_file(self, file_path):
        """Simple check if file is text file"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(512)
                # If NULL bytes exist, consider it binary
                if b'\x00' in chunk:
                    return False
                # Check control character ratio
                text_chars = sum(1 for byte in chunk if 32 <= byte < 127 or byte in (9, 10, 13))
                return text_chars / len(chunk) > 0.7 if chunk else False
        except:
            return False
    
    def view_selected_file(self):
        """View selected file in new window"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        file_index = selection[0]
        if file_index >= len(self.received_files):
            return
        
        file_path = self.received_files[file_index]
        filename = os.path.basename(file_path)
        
        # Create new window
        view_window = Toplevel(self.root)
        view_window.title(f"View File: {filename}")
        view_window.geometry("800x600")
        
        # Display file info
        info_frame = Frame(view_window, padx=10, pady=5)
        info_frame.pack(fill=X)
        
        file_size = os.path.getsize(file_path)
        info_label = Label(info_frame, text=f"File: {filename} | Size: {self.format_file_size(file_size)}",
                          font=DEFAULT_FONT)
        info_label.pack(anchor=W)
        
        # Display file content
        content_frame = Frame(view_window, padx=10, pady=10)
        content_frame.pack(fill=BOTH, expand=True)
        
        content_text = scrolledtext.ScrolledText(content_frame, font=MONOSPACE_FONT, wrap=WORD)
        content_text.pack(fill=BOTH, expand=True)
        
        # Read file content
        try:
            is_text = self.is_text_file(file_path)
            if is_text:
                encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                            content_text.insert(END, f.read())
                            break
                    except:
                        continue
            else:
                with open(file_path, 'rb') as f:
                    data = f.read()
                    content_text.insert(END, f"[Binary File - Hexadecimal]\n\n")
                    hex_str = data.hex()
                    formatted_hex = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
                    content_text.insert(END, formatted_hex)
        except Exception as e:
            content_text.insert(END, f"File read error: {e}")
        
        content_text.config(state=DISABLED)  # Read-only
    
    def start_server(self):
        """Start server"""
        if self.is_running:
            return
            
        try:
            host = self.host_entry.get().strip() or HOST
            port = int(self.port_entry.get().strip() or PORT)
            
            self.is_running = True
            self.start_btn.config(state=DISABLED)
            self.stop_btn.config(state=NORMAL)
            self.host_entry.config(state=DISABLED)
            self.port_entry.config(state=DISABLED)
            self.status_label.config(text=f"Server Running: {host or '0.0.0.0'}:{port}", fg="green")
            
            # Run server in separate thread
            self.server_thread = threading.Thread(target=self.server_loop, args=(host, port), daemon=True)
            self.server_thread.start()
            
        except ValueError:
            self.log("Error: Invalid port number.")
            messagebox.showerror("Input Error", "Port number must be a number.")
            self.is_running = False
            self.start_btn.config(state=NORMAL)
            self.stop_btn.config(state=DISABLED)
            self.host_entry.config(state=NORMAL)
            self.port_entry.config(state=NORMAL)
            self.status_label.config(text="Server Stopped", fg="red")
    
    def stop_server(self):
        """Stop server"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.host_entry.config(state=NORMAL)
        self.port_entry.config(state=NORMAL)
        self.status_label.config(text="Server Stopped", fg="red")
        self.connection_label.config(text="No Connection", fg="gray")
        self.log("Server stopped.")
    
    def server_loop(self, host, port):
        """Server main loop"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(1)
            
            self.log(f"TCP File Transfer Server Started")
            self.log(f"Waiting for connections... (Address: {host or '0.0.0.0'}:{port})")
            self.log(f"Receive directory: {os.path.abspath(RECEIVE_DIR)}")
            
            while self.is_running:
                try:
                    self.server_socket.settimeout(1.0)  # Check is_running every 1 second
                    conn, addr = self.server_socket.accept()
                    
                    self.log(f"\nClient connected: {addr}")
                    self.connection_label.config(text=f"Connected: {addr[0]}:{addr[1]}", fg="green")
                    
                    with conn:
                        if self.receive_file(conn):
                            self.log("File transfer successful")
                        else:
                            self.log("File transfer failed")
                    
                    self.log("Connection closed\n")
                    self.connection_label.config(text="No Connection", fg="gray")
                    
                except socket.timeout:
                    # Timeout is normal (for is_running check)
                    continue
                except OSError:
                    # When server socket is closed
                    if self.is_running:
                        self.log("Server socket error occurred")
                    break
                    
        except Exception as e:
            self.log(f"Error: Server error occurred: {e}")
            messagebox.showerror("Server Error", f"An error occurred while running the server:\n{e}")
        finally:
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
            self.is_running = False
            self.start_btn.config(state=NORMAL)
            self.stop_btn.config(state=DISABLED)
            self.host_entry.config(state=NORMAL)
            self.port_entry.config(state=NORMAL)
            self.status_label.config(text="Server Stopped", fg="red")
    
    def receive_file(self, conn):
        """Receive file from client and save"""
        try:
            # Step 1: Receive filename
            filename_data = b""
            while True:
                chunk = conn.recv(1)
                if not chunk:
                    return False
                if chunk == b'\0':  # NULL character indicates end of filename
                    break
                filename_data += chunk
            
            # Try UTF-8 decoding, fallback to other encodings
            try:
                filename = filename_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    filename = filename_data.decode('cp949')
                except UnicodeDecodeError:
                    filename = filename_data.decode('latin-1', errors='ignore')
            if not filename:
                self.log("Failed to receive filename.")
                return False
            
            self.log(f"Receiving file: {filename}")
            
            # Step 2: Send ready signal
            conn.sendall(b"READY")
            
            # Step 3: Receive file size
            file_size_data = b""
            while True:
                chunk = conn.recv(1)
                if not chunk:
                    return False
                if chunk == b'\0':  # NULL character indicates end of file size
                    break
                file_size_data += chunk
            
            try:
                # Try UTF-8 decoding
                try:
                    file_size_str = file_size_data.decode('utf-8')
                except UnicodeDecodeError:
                    file_size_str = file_size_data.decode('latin-1', errors='ignore')
                file_size = int(file_size_str)
            except ValueError:
                self.log("Error parsing file size")
                return False
            
            self.log(f"File size: {file_size} bytes")
            
            # Step 4: Receive file data
            file_path = os.path.join(RECEIVE_DIR, os.path.basename(filename))
            received_size = 0
            
            with open(file_path, 'wb') as f:
                while received_size < file_size:
                    remaining = file_size - received_size
                    chunk_size = min(BUFSIZE, remaining)
                    data = conn.recv(chunk_size)
                    if not data:
                        self.log("Connection unexpectedly closed.")
                        return False
                    f.write(data)
                    received_size += len(data)
                    # Display progress
                    progress = (received_size / file_size) * 100
                    progress_text = f"Receive Progress: {progress:.1f}% ({received_size:,}/{file_size:,} bytes)"
                    self.progress_label.config(text=progress_text)
                    
                    # Update progress bar
                    bar_width = int((received_size / file_size) * 100)
                    bar_text = "█" * bar_width + "░" * (100 - bar_width)
                    self.progress_bar.config(text=bar_text[:100])
                    
                    self.root.update()
            
            self.log(f"File receive completed: {file_path}")
            
            # Refresh file list
            self.refresh_file_list()
            
            # Step 5: Send success signal
            conn.sendall(b"SUCCESS")
            
            # Reset progress
            self.progress_label.config(text="")
            self.progress_bar.config(text="")
            
            return True
            
        except Exception as e:
            self.log(f"Error occurred while receiving file: {e}")
            try:
                conn.sendall(b"ERROR")
            except:
                pass
            return False

def main():
    root = Tk()
    app = TCPFileServer(root)
    root.mainloop()

if __name__ == "__main__":
    main()

