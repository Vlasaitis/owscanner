import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import subprocess
import queue
import owscanner


class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Overwatch Scanner")
        self.configure(bg="white")
        self.geometry("800x400")

        self.create_widgets()

    def create_widgets(self):
        self.select_video_label = tk.Label(
            self, text="Select Overwatch match to scan:", bg="white")
        self.select_video_label.grid(
            row=0, column=0, padx=10, pady=10, sticky="w")

        self.video_path_var = tk.StringVar()
        self.select_video_entry = tk.Entry(
            self, textvariable=self.video_path_var, width=40)
        self.select_video_entry.grid(
            row=1, column=0, padx=10, pady=10, sticky="w")

        self.browse_button = ctk.CTkButton(
            self, text="Browse", command=self.browse_video)
        self.browse_button.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.team_header = tk.Label(
            self, text="Enter {Color} teams names in order", bg="white")
        self.team_header.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.team_blue_label = tk.Label(self, text="TEAM BLUE", bg="white")
        self.team_blue_label.grid(
            row=3, column=0, padx=10, pady=10, sticky="w")

        self.team_red_label = tk.Label(self, text="TEAM RED", bg="white")
        self.team_red_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.blue_vars = [tk.StringVar() for _ in range(5)]
        self.red_vars = [tk.StringVar() for _ in range(5)]
        self.blue_entries = [
            tk.Entry(self, width=10, textvariable=var) for var in self.blue_vars]
        self.red_entries = [
            tk.Entry(self, width=10, textvariable=var) for var in self.red_vars]

        for i in range(5):
            self.blue_entries[i].grid(row=3, column=i + 1, padx=5, pady=5)
            self.red_entries[i].grid(row=4, column=i + 1, padx=5, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(
            self, variable=self.progress_var)

        self.progress_bar.grid(row=5, column=0, columnspan=6,
                               padx=10, pady=10, sticky="ew")

        self.start_processing_button = ctk.CTkButton(
            self, text="Start Processing", command=self.start_processing, state="normal")
        self.start_processing_button.grid(
            row=6, column=0, padx=10, pady=10, sticky="w")

        self.exit_button = ctk.CTkButton(self, text="Exit", command=self.quit)
        self.exit_button.grid(row=6, column=1, padx=10, pady=10, sticky="w")

    def browse_video(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4;*.mkv;*.avi")])
        if filepath:
            self.video_path_var.set(filepath)

    def start_processing(self):
        video_path = self.video_path_var.get()
        players = [entry.get()
                   for entry in self.blue_entries + self.red_entries]

        with open("scrimplayers.csv", "w") as f:
            f.write(",".join(players) + "\n")

        with open("video_path.csv", "w") as f:
            f.write(video_path + "\n")

        thread = threading.Thread(target=self.run_owscanner)
        thread.start()

    def run_owscanner(self):
        video_path = self.video_path_var.get()
        players = [entry.get()
                   for entry in self.blue_entries + self.red_entries]

        # Write players to the file
        with open("scrimplayers.csv", "w") as f:
            f.write(",".join(players) + "\n")

        players_file_path = "scrimplayers.csv"

        progress_queue = queue.Queue()
        thread = threading.Thread(target=owscanner.main, args=(
            video_path, players_file_path, progress_queue))
        thread.start()

        progress_thread = threading.Thread(
            target=self.update_progress_from_queue, args=(progress_queue,))
        progress_thread.start()

    def update_progress(self, current_frame_nr, total_frames):
        progress = (current_frame_nr / total_frames)
        self.progress_var.set(progress)

    def update_progress_from_queue(self, progress_queue):
        while True:
            try:
                current_frame_nr, total_frames = progress_queue.get(
                    block=True, timeout=1)
                self.update_progress(current_frame_nr, total_frames)
                if current_frame_nr == total_frames:
                    break
            except queue.Empty:
                pass


def main():
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
