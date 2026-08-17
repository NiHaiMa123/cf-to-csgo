# -*- coding: utf-8 -*-
"""沙盒冒烟检查逻辑：L0 环境 / L1 语法 / L2 冒烟。

所有检查都在临时沙盒内进行：通过环境变量把脚本的输入/输出目录
重定向到沙盒，绝不触碰真实的 data/ 与游戏目录。
"""
import os
import struct
import subprocess
import sys
import wave

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")


# ---------------------------------------------------------------------------
# L0 环境自检
# ---------------------------------------------------------------------------
def check_env(logger):
    logger.section("L0 环境自检")
    logger.info(f"Python {sys.version.split()[0]}  ({sys.executable})")

    if shutil_which("ffmpeg"):
        logger.ok("ffmpeg 可用（package_tts_migi / convert_audio 依赖）")
    else:
        logger.fail("ffmpeg 不在 PATH（package_tts_migi / convert_audio 需要）")

    vgs = os.path.join(PROJECT_DIR, "tools", "vgmstream", "vgmstream-cli.exe")
    if os.path.exists(vgs):
        logger.ok(f"vgmstream-cli.exe 存在：{vgs}")
    else:
        logger.fail(f"vgmstream-cli.exe 缺失：{vgs}")

    try:
        import vpk  # noqa: F401
        logger.ok("vpk 库可导入（unpack_vpk_voices 依赖）")
    except ImportError:
        logger.fail("vpk 库不可导入（unpack_vpk_voices 需要：pip install vpk）")

    cf = os.environ.get("CF2_CF_DIR", r"D:\Program Files\CF(2)")
    if os.path.isdir(cf):
        logger.ok(f"CF 目录存在：{cf}")
    else:
        logger.warn(f"CF 目录不存在：{cf}（解包类脚本将无输入）")

    game = os.environ.get("CF2_GAME_DIR", r"D:\steam\steamapps\common\csgo legacy")
    if os.path.isdir(game):
        logger.ok(f"CS:GO 游戏目录存在：{game}")
    else:
        logger.warn(f"CS:GO 游戏目录不存在：{game}（打包/GSI 脚本将无输入）")


def shutil_which(name):
    import shutil
    return shutil.which(name)


# ---------------------------------------------------------------------------
# L1 语法检查
# ---------------------------------------------------------------------------
def _iter_scripts():
    for root, _, files in os.walk(SCRIPTS_DIR):
        for f in sorted(files):
            if f.endswith(".py"):
                yield os.path.join(root, f)


def check_syntax(logger):
    logger.section("L1 脚本语法检查")
    import py_compile
    count = 0
    for path in _iter_scripts():
        count += 1
        rel = os.path.relpath(path, PROJECT_DIR)
        try:
            py_compile.compile(path, doraise=True)
            logger.ok(f"语法 OK：{rel}")
        except py_compile.PyCompileError as e:
            logger.fail(f"语法错误：{rel} - {e}")
    logger.info(f"共检查 {count} 个脚本")


# ---------------------------------------------------------------------------
# 冒烟辅助
# ---------------------------------------------------------------------------
def _make_wav(path, seconds=0.1, rate=8000):
    """造一个最小但合法的 16-bit mono WAV。"""
    import math
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = int(rate * seconds)
    frames = b"".join(
        struct.pack("<h", int(12000 * math.sin(2 * math.pi * 440 * i / rate)))
        for i in range(n)
    )
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)


def _make_min_vpk(path):
    """造一个最小的空 VPK（signature + version=1 + tree_size=0）。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x55AA1234, 1, 0))
        f.write(b"\x00")


def _run_script(logger, rel, env, expect_outputs=(), expect_nonempty_dirs=()):
    """以子进程运行脚本，校验退出码与预期产出。"""
    script = os.path.join(SCRIPTS_DIR, rel)
    proc = subprocess.run([sys.executable, script], env=env,
                          capture_output=True, text=True, timeout=120)
    base = rel
    if proc.returncode != 0:
        logger.fail(f"{base} 运行失败，退出码 {proc.returncode}")
        tail = ((proc.stdout or "") + (proc.stderr or ""))[-500:].strip()
        if tail:
            logger.info(f"{base} 输出尾部：{tail[:600]}")
        return
    for out in expect_outputs:
        if not os.path.exists(out):
            logger.fail(f"{base} 运行成功但缺少预期输出：{out}")
            return
    for d in expect_nonempty_dirs:
        if not (os.path.isdir(d) and os.listdir(d)):
            logger.fail(f"{base} 运行成功但目录为空：{d}")
            return
    logger.ok(f"{base} 冒烟通过")


def _build_sandbox_env(sandbox):
    data = os.path.join(sandbox, "data")
    game = os.path.join(sandbox, "game")
    cf = os.path.join(sandbox, "cf")
    for d in (data, game, cf):
        os.makedirs(d, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "CF2_DATA_DIR": data,
        "CF2_GAME_DIR": game,
        "CF2_CF_DIR": cf,
        "CF2_LOG_DIR": os.path.join(sandbox, "logs"),
    })
    return env, data, game, cf


# ---------------------------------------------------------------------------
# L2 沙盒冒烟
# ---------------------------------------------------------------------------
def check_smoke(logger, sandbox):
    logger.section("L2 沙盒冒烟")
    env, data, game, cf = _build_sandbox_env(sandbox)

    # clean_wavs：造 1 个 wav，断言 Snd2_Cleaned 产出
    _make_wav(os.path.join(cf, "rez", "Snd2", "sample.wav"))
    _run_script(logger, "audio_clean/clean_wavs.py", env,
                expect_outputs=(os.path.join(data, "Snd2_Cleaned", "sample.wav"),))

    # categorize_voices：造 2 个 BL_C 语音，断言 Categorized/BL_C 非空
    vc = os.path.join(data, "FMOD_Voices", "Voice_CN")
    _make_wav(os.path.join(vc, "16800_RADIOMESSAGE_BL_C_1_1.wav"))
    _make_wav(os.path.join(vc, "16801_RADIOMESSAGE_BL_C_1_2.wav"))
    _run_script(logger, "audio_clean/categorize_voices.py", env,
                expect_nonempty_dirs=(os.path.join(vc, "Categorized", "BL_C"),))

    # parse_vpk：造最小空 VPK，脚本应能正常读取并退出
    _make_min_vpk(os.path.join(game, "csgo", "pak01_dir.vpk"))
    _run_script(logger, "csgo_pack/parse_vpk.py", env)

    # unpack_vpk_voices：造最小空 VPK（依赖 vpk 库），空包应正常遍历
    _make_min_vpk(os.path.join(game, "csgo", "pak01_dir.vpk"))
    _run_script(logger, "csgo_pack/unpack_vpk_voices.py", env)

    # package_tts_migi：造 1 个 TTS wav（依赖 ffmpeg），分发目标为空也应正常结束
    _make_wav(os.path.join(data, "rvc", "tts", "radio_letsgo01.wav"))
    _run_script(logger, "csgo_pack/package_tts_migi.py", env)

    # 其余脚本：空输入下不崩溃
    for rel in [
        "cf_extract/extract_all.py",
        "cf_extract/extract_fmod.py",
        "csgo_pack/convert_audio.py",
        "csgo_pack/fix_planting_voices.py",
    ]:
        _run_script(logger, rel, env)

    # gsi 脚本：只做模块加载检查（服务器会阻塞，不实跑）
    for rel in ["gsi/gsi_voice_bot.py", "gsi/gsi_voice_bot_debug.py"]:
        script = os.path.join(SCRIPTS_DIR, rel)
        code = f"import runpy; runpy.run_path({script!r})"
        proc = subprocess.run([sys.executable, "-c", code], env=env,
                              capture_output=True, text=True, timeout=60)
        if proc.returncode == 0:
            logger.ok(f"{rel} 模块可加载")
        else:
            logger.fail(f"{rel} 模块加载失败，退出码 {proc.returncode}")
            tail = ((proc.stdout or "") + (proc.stderr or ""))[-400:].strip()
            if tail:
                logger.info(f"{rel} 输出尾部：{tail[:500]}")
