#!/usr/bin/env python3
"""cross-border-investment-financing-risk-control 技能验证脚本。

断言"分析产出=合规成立"而非"动作已执行"：
- GOOD 样例：含全部合规要素（ODI 审批链/敏感类核查/风险量化/退出机制/坑位引用），且无违规 → exit 0
- BAD 样例：命中任一违规模式（分拆出境/规避监管/跳过备案/代持/先斩后奏）→ exit 1

退出码契约：0=通过，1=存在错误，2=文件错误。

用法：
  python scripts/validate.py tests/sample_good.md   # 期望 exit 0
  python scripts/validate.py tests/sample_bad.md    # 期望 exit 1
"""
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_FILE_ERROR = 2


def read_sample(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        sys.exit(EXIT_FILE_ERROR)
    return p.read_text(encoding="utf-8")


GOOD_REQUIREMENTS = [
    (r"ODI|备案|核准", "缺少 ODI 审批链核查（发改/商务/外汇）"),
    (r"敏感(类|国别|行业)", "缺少敏感类核查（国别/行业）"),
    (r"37\s*号文", "缺少 37 号文返程投资登记检查"),
    (r"风险.{0,12}(量化|识别|评估)|量化.{0,8}风险", "缺少风险量化"),
    (r"退出(机制|方案|安排)|回购", "缺少退出机制"),
    (r"gotchas|坑位|红线", "缺少 gotchas 坑位引用"),
]

BAD_VIOLATIONS = [
    (r"分批.{0,4}出境|分拆.{0,6}(购汇|汇出|出境|汇款)", "命中违规：分拆/分批出境规避监管"),
    (r"避免.{0,8}(监管|审查|关注|触发)", "命中违规：以规避监管为策略"),
    (r"(跳过|无需|免办|不必).{0,6}(备案|ODI|审批|登记)", "命中违规：跳过备案/审批"),
    (r"代持|借.{0,4}(他人|朋友).{0,6}(额度|名义)", "命中违规：代持/借额度规避"),
    (r"(先|资金?先).{0,6}(出境|汇出|划转).{0,10}(后|再).{0,6}(补|办|备)", "命中违规：先出境后补手续"),
    (r"借用.{0,6}(额度|身份证)", "命中违规：借用他人额度"),
]


def find_violations(text: str) -> list:
    hits = []
    for pattern, msg in BAD_VIOLATIONS:
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(msg)
    return hits


def find_missing_good(text: str) -> list:
    missing = []
    for pattern, msg in GOOD_REQUIREMENTS:
        if not re.search(pattern, text, re.IGNORECASE):
            missing.append(msg)
    return missing


def main():
    if len(sys.argv) < 2:
        print("用法: validate.py <sample.md>", file=sys.stderr)
        sys.exit(EXIT_FILE_ERROR)

    sample_path = sys.argv[1]
    text = read_sample(sample_path)
    fname = Path(sample_path).name.lower()
    is_bad = "bad" in fname

    errors = []

    violations = find_violations(text)
    if is_bad:
        if not violations:
            errors.append("BAD 样例未命中任何已知违规模式（应至少命中一条）")
        else:
            errors.append(f"BAD 样例命中 {len(violations)} 条违规（预期失败）：{'; '.join(violations)}")
    else:
        if violations:
            errors.append(f"GOOD 样例命中违规（不应有）：{'; '.join(violations)}")
        missing = find_missing_good(text)
        errors.extend(missing)

    if errors:
        print(f"验证失败（{len(errors)} 项）：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(EXIT_FAIL)

    print("验证通过")
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
