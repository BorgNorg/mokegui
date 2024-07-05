import customtkinter as ctk
from tkinter import filedialog


class MOKEGUI:

    def __init__(self):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.app = ctk.CTk()
        self.app.geometry("750x475")
        self.app.title("MOKE")

        frame = ctk.CTkFrame(master=self.app)
        frame.grid(row=0, column=0, sticky="nsew")

        self.start_button = ctk.CTkButton(master=self.app, text="Start", command=self.toggle)
        self.start_button.place(relx=0.75, rely=0.85, anchor=ctk.CENTER, relwidth=0.2, relheight=0.1)

        self.directory_button = ctk.CTkButton(master=self.app, text="Save Directory", command=self.save_directory)
        self.directory_button.place(relx=0.50, rely=0.85, anchor=ctk.CENTER, relwidth=0.2, relheight=0.1)

        self.calibration_button = ctk.CTkButton(master=self.app, text="Calibration File", command=self.calibration_file)
        self.calibration_button.place(relx=0.25, rely=0.85, anchor=ctk.CENTER, relwidth=0.2, relheight=0.1)

        self.maxV = ctk.CTkTextbox(master=frame, height=20, width=80)
        self.maxV.grid(row=0, column=1, padx=10, pady=5)

        self.minV = ctk.CTkTextbox(master=frame, height=20, width=80)
        self.minV.grid(row=1, column=1, padx=10, pady=5)

        self.stepV = ctk.CTkTextbox(master=frame, height=20, width=80)
        self.stepV.grid(row=2, column=1, padx=10, pady=5)

        self.label_max = ctk.CTkLabel(master=frame, text="Max Voltage (V)")
        self.label_max.grid(row=0, column=0, padx=10, pady=5)

        self.label_min = ctk.CTkLabel(master=frame, text="Min Voltage (V)")
        self.label_min.grid(row=1, column=0, padx=10, pady=5)

        self.label_step = ctk.CTkLabel(master=frame, text="Step Voltage (V)")
        self.label_step.grid(row=2, column=0, padx=10, pady=5)

        self.app.mainloop()

    def toggle(self):
        current = self.start_button.cget("text")
        if current == "Start":
            self.start_button.configure(text="Stop")
        else:
            self.start_button.configure(text="Start")

    def save_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            print(f"Selected Directory: {directory}")
            self.directory_button.configure(text=directory)

    def calibration_file(self):
        calibration = filedialog.askopenfilename()
        if calibration:
            print(f"Selected Calibration File: {calibration}")
            self.calibration_button.configure(text=calibration)


MOKEGUI()
