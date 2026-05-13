
import os
import shutil
from datetime import datetime
import frappe
from frappe.utils.backups import new_backup

def auto_backup():
    """Create SQL-only backup inside private/auto_backups/YYYY-MM-DD"""
    
    # Ensure we are in a site context
    if not frappe.local.site:
        frappe.logger().error("❌ No site context found.")
        return

    site = frappe.local.site
    now = datetime.now()
    
    # Use ISO format for better folder sorting: YYYY-MM-DD
    date_folder = now.strftime('%Y-%m-%d')
    time_str = now.strftime("%H-%M-%S")

    # Path: sites/{site}/private/auto_backups/{date}
    backup_dir = frappe.get_site_path("private", "auto_backups", date_folder)
    os.makedirs(backup_dir, exist_ok=True)

    try:
        # Generate DB backup (ignore_files=True skips public/private files)
        backup = new_backup(ignore_files=True)
        db_path = backup.backup_path_db

        if db_path and os.path.exists(db_path):
            new_db_filename = f"{site}_db_{time_str}.sql.gz"
            dest_path = os.path.join(backup_dir, new_db_filename)

            # Move or Copy? 
            # If you use copy2, remember to occasionally clean /private/backups
            shutil.copy2(db_path, dest_path)

            frappe.logger().info(f"✅ Backup successful: {dest_path}")
        else:
            frappe.logger().error("❌ Backup file was not generated.")

    except Exception as e:
        frappe.logger().error(f"❌ Backup failed: {str(e)}")