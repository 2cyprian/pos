import asyncio
from app.database import SessionLocal
from app import models
from app.services.snmp_svc import fetch_printer_counter

# Single global task holder for the watchdog
watchdog_task = None


async def run_snmp_watchdog():
    """
    Periodically polls printers via SNMP, updates counters, and logs changes.
    Runs until cancelled.
    """
    while True:
        db = SessionLocal()
        try:
            printers = db.query(models.Printer).all()
            for printer in printers:
                print(f" [WATCHDOG] Checking printer: {printer.name} ({printer.ip_address})")
                count = await fetch_printer_counter(printer.ip_address)
                if count is not None:
                    if count > printer.total_page_counter:
                        pages_printed = count - printer.total_page_counter
                        printer.total_page_counter = count
                        db.add(printer)
                        db.commit()
                        db.refresh(printer)

                        log_entry = models.PrinterLog(
                            printer_id=printer.id,
                            page_count=count,
                            notes=f"Pages printed: {pages_printed} | Total: {count}"
                        )
                        db.add(log_entry)
                        db.commit()
                        print(f" [WATCHDOG] Printer {printer.name} Total Count Updated: {count}")
                    else:
                        print(f" [WATCHDOG] Printer {printer.name} Total Count (no change): {count}")
                else:
                    print(f" [WATCHDOG] Failed to fetch counter for {printer.name} ({printer.ip_address})")
        except Exception as e:
            print(f" [WATCHDOG ERROR] {e}")
        finally:
            db.close()

        await asyncio.sleep(60)


def is_watchdog_running() -> bool:
    global watchdog_task
    return watchdog_task is not None and not watchdog_task.done()


def start_watchdog() -> str:
    """Starts the watchdog if not already running."""
    global watchdog_task
    if is_watchdog_running():
        return "already_running"
    watchdog_task = asyncio.create_task(run_snmp_watchdog())
    return "started"


async def stop_watchdog() -> str:
    """Stops the watchdog if running."""
    global watchdog_task
    if not is_watchdog_running():
        return "not_running"
    watchdog_task.cancel()
    await asyncio.sleep(0.1)
    return "stopped"
