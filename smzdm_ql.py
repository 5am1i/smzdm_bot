"""
什么值得买自动签到脚本
项目地址: https://github.com/5am1i/smzdm_bot/
0 9 * * * smzdm_ql.py
const $ = new Env("什么值得买签到");
"""

import os
import sys
from pathlib import Path

ql_repo_dir = Path("/ql/data/repo/")
repo_name = "5am1i_smzdm_bot"
repo_dir = Path(ql_repo_dir, repo_name)


def main():
    # 切换到项目目录
    os.chdir(str(repo_dir))
    
    # 兼容青龙平台的环境变量命名
    # 将 ANDROID_COOKIE 映射到 SMZDM_COOKIE
    if "ANDROID_COOKIE" in os.environ and "SMZDM_COOKIE" not in os.environ:
        os.environ["SMZDM_COOKIE"] = os.environ["ANDROID_COOKIE"]
    
    # 兼容其他环境变量
    env_mapping = {
        "SK": "SMZDM_SK",
        "PUSH_PLUS_TOKEN": "SMZDM_PUSH_PLUS_TOKEN",
        "SC_KEY": "SMZDM_SC_KEY",
        "WECOM_BOT_WEBHOOK": "SMZDM_WECOM_WEBHOOK",
        "TG_BOT_TOKEN": "SMZDM_TG_BOT_TOKEN",
        "TG_USER_ID": "SMZDM_TG_USER_ID",
        "TG_BOT_API": "SMZDM_TG_API_BASE",
        "SCH_HOUR": "SMZDM_SCH_HOUR",
        "SCH_MINUTE": "SMZDM_SCH_MINUTE",
    }
    
    for old_key, new_key in env_mapping.items():
        if old_key in os.environ and new_key not in os.environ:
            os.environ[new_key] = os.environ[old_key]
    
    # 添加 src 目录到 Python 路径
    src_dir = repo_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    # 安装依赖（忽略 pip 警告和版本检查）
    os.system(
        "pip3 install -q --upgrade pip 2>/dev/null; "
        "pip3 install -q --no-warn-script-location "
        "apscheduler>=3.10.1 httpx>=0.27.0 loguru>=0.7.0 "
        "pycryptodome>=3.20.0 pydantic>=2.0.0 pydantic-settings>=2.0.0 typer>=0.12.0 "
        "2>/dev/null || true"
    )
    
    # 直接运行主函数，避免安装包
    from smzdm_bot.main import main as run_main
    sys.exit(run_main())


if __name__ == "__main__":
    main()
