import os
import sys
import platform
import psutil
import sqlite3

def system_check():
    print("Chennai Medical AI Pre-Flight Check:")
    print("-" * 40)
    
    # 1. Python version check
    py_version = sys.version_info
    print(f"✅ Python: {platform.python_version()}") if py_version >= (3, 9) else print(f"❌ Python 3.9+ required (Current: {platform.python_version()})")
    
    # 2. Memory check
    mem = psutil.virtual_memory()
    print(f"✅ Memory: {mem.available/1024**3:.1f}GB available") if mem.available > 2*1024**3 else print(f"❌ Insufficient RAM: {mem.available/1024**3:.1f}GB (4GB+ recommended)")
    
    # 3. Disk space check
    disk = psutil.disk_usage('/')
    print(f"✅ Disk: {disk.free/1024**3:.1f}GB free") if disk.free > 5*1024**3 else print(f"❌ Low disk space: {disk.free/1024**3:.1f}GB (5GB+ recommended)")
    
    # 4. Database check
    try:
        conn = sqlite3.connect('patient_db.db')
        print("✅ Database: Access verified")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
    
    # 5. Critical files check
    required_files = ['src/main.py', 'src/nlp_processor.py']
    missing = [f for f in required_files if not os.path.exists(f)]
    print("✅ Critical files: Present") if not missing else print(f"❌ Missing files: {', '.join(missing)}")
    
    print("-" * 40)
    print("System ready for Chennai deployment!" if all([
        py_version >= (3, 9),
        mem.available > 2*1024**3,
        disk.free > 5*1024**3,
        not missing
    ]) else "Fix issues before deployment")

if __name__ == "__main__":
    system_check()