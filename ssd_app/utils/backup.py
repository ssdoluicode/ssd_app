


# def auto_backup():
#     """Only SQL backup + cleanup"""

#     site = frappe.local.site

#     # Only DB backup
#     backup = new_backup(ignore_files=True)

#     # Date format (with time to avoid overwrite)
#     date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#     # Backup directory
#     backup_dir = frappe.get_site_path("private", "backups")

#     # ------------------ DATABASE ONLY ------------------
#     if backup.backup_path_db and os.path.exists(backup.backup_path_db):
#         new_db = os.path.join(backup_dir, f"db_{date_str}.sql.gz")
#         shutil.move(backup.backup_path_db, new_db)


#     frappe.logger().info(f"✅ SQL Backup Completed for {site} on {date_str}")


import os
import shutil
from datetime import datetime

import frappe
from frappe.utils.backups import new_backup


def auto_backup():
    """Create SQL-only backup in private/auto_backups without deleting old backups"""

    site = frappe.local.site

    # Create DB-only backup (no files)
    backup = new_backup(ignore_files=True)

    # Timestamp to avoid overwrite
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Custom backup directory
    backup_dir = frappe.get_site_path("private", "auto_backups")

    # Create folder if not exists
    os.makedirs(backup_dir, exist_ok=True)

    # ------------------ DATABASE BACKUP ------------------
    if backup.backup_path_db and os.path.exists(backup.backup_path_db):

        # Keep .sql.gz format compatible with:
        # bench --site <site-name> restore <file.sql.gz>
        new_db_path = os.path.join(
            backup_dir,
            f"{site}_db_{date_str}.sql.gz"
        )

        # Move generated backup to custom folder
        shutil.move(backup.backup_path_db, new_db_path)

        frappe.logger().info(
            f"✅ SQL Backup Completed: {new_db_path}"
        )

    else:
        frappe.logger().error(
            f"❌ SQL Backup Failed for {site}"
        )
