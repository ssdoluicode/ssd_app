import frappe
import os
import shutil
from datetime import datetime, timedelta
from frappe.utils.backups import new_backup


def auto_backup():
    """Only SQL backup + cleanup"""

    site = frappe.local.site

    # Only DB backup
    backup = new_backup(ignore_files=True)

    # Date format (with time to avoid overwrite)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Backup directory
    backup_dir = frappe.get_site_path("private", "backups")

    # ------------------ DATABASE ONLY ------------------
    if backup.backup_path_db and os.path.exists(backup.backup_path_db):
        new_db = os.path.join(backup_dir, f"db_{date_str}.sql.gz")
        shutil.move(backup.backup_path_db, new_db)

    # # Cleanup old backups (30 days)
    # delete_old_backups(backup_dir, days=30)

    frappe.logger().info(f"✅ SQL Backup Completed for {site} on {date_str}")


def delete_old_backups(folder, days=30):
    """Delete files older than X days"""

    now = datetime.now()
    cutoff = now - timedelta(days=days)

    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)

        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

            if file_time < cutoff:
                os.remove(file_path)