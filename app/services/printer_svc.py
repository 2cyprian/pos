import os
import platform
import subprocess


def send_to_printer(file_path: str, printer_name: str = None):
    """
    Sends a file directly to the OS print queue.
    """
    system_name = platform.system()
    
    try:
        # --- WINDOWS LOGIC ---
        if system_name == "Windows":
            if printer_name:
                # Advanced: Use specific printer via Command Line
                # Requires PDFtoPrinter or similar utility for silent printing
                # Here is a generic 'default printer' command:
                os.startfile(file_path, "print")
            else:
                os.startfile(file_path, "print")
                
        # --- LINUX / MAC (CUPS) LOGIC ---
        else:
            # Construct command: lp -d "Printer_Name" "filename.pdf"
            command = ["lp"]
            if printer_name:
                command.extend(["-d", printer_name])
            command.append(file_path)
            
            subprocess.run(command, check=True)
            
        return {"status": "success", "message": "Sent to print queue"}

    except Exception as e:
        return {"status": "error", "message": str(e)}