"""Klik dua kali untuk membuka jendela simulasi Python."""
from pathlib import Path
import runpy
import sys

code = Path(__file__).resolve().parent / 'kode'
sys.path.insert(0, str(code))
try:
    runpy.run_path(str(code / 'simulasi_interaktif.py'), run_name='__main__')
except (Exception, SystemExit) as exc:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror('Simulasi Optik', str(exc))
    root.destroy()
