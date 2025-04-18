import subprocess
import os


def start_files():
    # 直接写入文件的完整路径
    a_file = r"C:\OneDrive\ChenJun\OneDrive - MSFT\2.Game\Game\Escape From Tarkov\3.11.3.0.16.1.3.35392 Fika\Server\SPT.Server.exe"  # 替换为实际路径
    b_file = r"C:\OneDrive\ChenJun\OneDrive - MSFT\2.Game\Game\Escape From Tarkov\3.11.3.0.16.1.3.35392 Fika\Server\Start_headless_680052ebd1e1f136f8002254.ps1"  # 替换为实际路径

    a_dir = os.path.dirname(a_file)
    b_dir = os.path.dirname(b_file)

    print(f"A文件路径: {a_file}")
    print(f"B文件路径: {b_file}")
    print(f"A文件目录: {a_dir}")
    print(f"B文件目录: {b_dir}")

    if os.path.exists(a_file) and os.path.exists(b_file):
        # 启动 A 时设置工作目录
        subprocess.Popen(a_file, cwd=a_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)

        # 启动 B（PowerShell）时设置工作目录
        subprocess.Popen(["powershell", "-NoExit", "-File", b_file], cwd=b_dir,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)

        print("成功启动 A 和 B 文件。")
    else:
        print("文件 A 或 B 不存在，请检查文件路径。")


if __name__ == "__main__":
    start_files()
