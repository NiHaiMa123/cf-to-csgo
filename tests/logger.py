# -*- coding: utf-8 -*-
"""轻量日志工具：控制台 + 文件双写，供 run_smoke.py 使用。"""
import os
import sys
import datetime

# 控制台统一 UTF-8 输出，避免 Windows 终端按 GBK 显示中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class Logger:
    """写带时间戳的日志到文件，同时镜像到控制台。"""

    def __init__(self, log_dir, name="smoke"):
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(log_dir, f"{ts}_{name}.log")
        self.file = open(self.path, "a", encoding="utf-8")
        self.counts = {"PASS": 0, "FAIL": 0, "SKIP": 0, "WARN": 0}
        self.failures = []

    def _write(self, level, message):
        line = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{level}] {message}"
        print(line)
        self.file.write(line + "\n")
        self.file.flush()

    def section(self, title):
        bar = "=" * 60
        self._write("====", bar)
        self._write("====", title)
        self._write("====", bar)

    def info(self, message):
        self._write("INFO", message)

    def ok(self, message):
        self.counts["PASS"] += 1
        self._write("PASS", message)

    def warn(self, message):
        self.counts["WARN"] += 1
        self._write("WARN", message)

    def fail(self, message):
        self.counts["FAIL"] += 1
        self.failures.append(message)
        self._write("FAIL", message)

    def skip(self, message):
        self.counts["SKIP"] += 1
        self._write("SKIP", message)

    def summary(self):
        """写汇总，返回失败数。"""
        total = sum(self.counts.values())
        self._write("SUMMARY",
                    f"通过 {self.counts['PASS']} / 失败 {self.counts['FAIL']} / "
                    f"跳过 {self.counts['SKIP']} / 警告 {self.counts['WARN']}（共 {total} 项）")
        for f in self.failures:
            self._write("DETAIL", f"  失败项：{f}")
        self.file.close()
        return self.counts["FAIL"]
