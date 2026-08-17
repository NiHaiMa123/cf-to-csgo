# -*- coding: utf-8 -*-
"""
共享路径解析模块。

所有脚本的输入/输出路径统一从这里获取：
- 默认值 = 项目内固定路径（与迁移前一致，行为不变）；
- 支持环境变量覆盖，供 tests/run_smoke.py 在沙盒测试时注入临时目录，
  使脚本输出全部落到沙盒内，不污染真实的 data/ 与游戏目录。

可覆盖的环境变量：
  CF2_PROJECT_DIR  项目根目录（默认 scripts/ 的父目录）
  CF2_DATA_DIR     data 数据目录
  CF2_LOG_DIR      logs 日志目录
  CF2_GAME_DIR     CS:GO 游戏根目录（Steam csgo legacy）
  CF2_CF_DIR       CF 游戏安装目录
  CF2_VGMSTREAM    vgmstream-cli.exe 完整路径
"""
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)   # scripts 的父目录 = 项目根


def _resolve(env_name, default):
    return os.environ.get(env_name, default)


def project_dir():
    """项目根目录。"""
    return _resolve("CF2_PROJECT_DIR", _PROJECT_DIR)


def data_dir():
    """中间/成品数据目录。"""
    return _resolve("CF2_DATA_DIR", os.path.join(project_dir(), "data"))


def log_dir():
    """日志输出目录（测试后唯一保留物）。"""
    return _resolve("CF2_LOG_DIR", os.path.join(project_dir(), "logs"))


def game_dir():
    """CS:GO 游戏根目录（Steam csgo legacy）。"""
    return _resolve("CF2_GAME_DIR", r"D:\steam\steamapps\common\csgo legacy")


def cf_dir():
    """CF 游戏安装目录（含 rez/）。"""
    return _resolve("CF2_CF_DIR", r"D:\Program Files\CF(2)")


def vgmstream():
    """vgmstream-cli.exe 完整路径。"""
    return _resolve("CF2_VGMSTREAM",
                    os.path.join(project_dir(), "tools", "vgmstream", "vgmstream-cli.exe"))
