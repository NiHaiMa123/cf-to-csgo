# -*- coding: utf-8 -*-
"""CF→CS:GO 项目沙盒冒烟测试主入口。

用法：
    python tests\\run_smoke.py                  # 跑全部，测完自动清理沙盒
    python tests\\run_smoke.py --keep-tmp       # 保留沙盒目录便于排查
    python tests\\run_smoke.py --log-dir DIR    # 指定日志目录（默认 logs/）

流程：环境自检(L0) → 语法检查(L1) → 沙盒冒烟(L2)，全部写入 logs/ 下带时间戳的
log；无论成败，结束都会删除沙盒目录（data/tmp/<run-id>），只保留 log。
有失败项时退出码非 0，便于 agent 判断。
"""
import argparse
import datetime
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

import logger as logger_mod  # noqa: E402
import checks  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="CF→CS:GO 项目沙盒冒烟测试")
    ap.add_argument("--keep-tmp", action="store_true", help="保留沙盒目录，便于排查")
    ap.add_argument("--log-dir", default=os.path.join(PROJECT_DIR, "logs"),
                    help="日志输出目录（默认 logs/）")
    args = ap.parse_args()

    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sandbox = os.path.join(PROJECT_DIR, "data", "tmp", run_id)
    os.makedirs(sandbox, exist_ok=True)

    log = logger_mod.Logger(args.log_dir)
    log.info(f"项目根：{PROJECT_DIR}")
    log.info(f"沙盒目录：{sandbox}")

    try:
        checks.check_env(log)
        checks.check_syntax(log)
        checks.check_smoke(log, sandbox)
    except Exception as e:
        log.fail(f"测试框架异常：{e!r}")
    finally:
        if args.keep_tmp:
            log.info(f"已保留沙盒（--keep-tmp）：{sandbox}")
        else:
            shutil.rmtree(sandbox, ignore_errors=True)
            log.info("沙盒已清理，只保留日志。")

    log.info(f"日志已写入：{log.path}")
    failures = log.summary()
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
