import frappe
import os
import shutil
from datetime import datetime, timedelta


def auto_backup():
    """Run daily backup with custom filename + cleanup"""

    site = frappe.local.site

    # Run backup (DB + files)
    backup = frappe.utils.backups.new_backup(ignore_files=False)

    # Date format
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Backup directory
    backup_dir = frappe.get_site_path("private", "backups")

    # ------------------ DATABASE ------------------
    if backup.backup_path_db and os.path.exists(backup.backup_path_db):
        new_db = os.path.join(backup_dir, f"backup_{date_str}.sql.gz")
        shutil.move(backup.backup_path_db, new_db)

    # ------------------ PUBLIC FILES ------------------
    if backup.backup_path_files and os.path.exists(backup.backup_path_files):
        new_files = os.path.join(backup_dir, f"files_{date_str}.tar")
        shutil.move(backup.backup_path_files, new_files)

    # ------------------ PRIVATE FILES ------------------
    if backup.backup_path_private_files and os.path.exists(backup.backup_path_private_files):
        new_private = os.path.join(backup_dir, f"private_files_{date_str}.tar")
        shutil.move(backup.backup_path_private_files, new_private)

    # ------------------ CLEAN OLD BACKUPS ------------------
    delete_old_backups(backup_dir, days=30)

    frappe.logger().info(f"✅ Auto Backup Completed for {site} on {date_str}")


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