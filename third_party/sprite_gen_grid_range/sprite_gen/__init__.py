# SPDX-License-Identifier: Apache-2.0
"""只覆盖格距搜索参数；其余sprite-gen模块仍由已安装技能提供。"""
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
from sprite_gen import _deps as _deps  # 保留上游NumPy依赖门槛。
