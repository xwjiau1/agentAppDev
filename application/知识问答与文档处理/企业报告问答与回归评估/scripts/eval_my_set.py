# -*- coding: utf-8 -*-
"""my_set 评测脚本：将 pipeline 产出的 answers JSON 与标准答案比对。

评测维度：
  1. 答案正确率（按题型 number/boolean/name/names/comparative 分别统计 + 总准确率）
  2. 防幻觉题（量子跳动，不在库中）是否正确拒答（value=null / N/A）
  3. 引用合规率：成功作答的题是否都带了非空 references
归一化规则：
  number   提取数值做容差比较（±0.05，占比题兼容 0.62 vs 62 两种写法）
  boolean  兼容 True/False/"是"/"否"/"提及"/"未提及"
  name     字符串包含
  names    每个期望人名都必须出现
  comparative 答案字符串包含期望公司名
"""
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MY_SET = ROOT / "data" / "my_set"

# 标准答案（与 scripts/build_my_set.py 中年报正文一一对应）
GOLD = [
    {"q": "营业收入是多少亿元", "company": "星辰科技", "kind": "number", "expect": 58.6},
    {"q": "研发投入是多少亿元", "company": "蓝海能源", "kind": "number", "expect": 4.2},
    {"q": "净利润是多少亿元", "company": "峰瑞制药", "kind": "number", "expect": 5.1},
    {"q": "研发人员占员工总数的比例", "company": "星辰科技", "kind": "number", "expect": 62, "pct": True},
    {"q": "是否在2024年宣布了分红政策变更", "company": "峰瑞制药", "kind": "boolean", "expect": True},
    {"q": "是否提及并购事项", "company": "星辰科技", "kind": "boolean", "expect": False},
    {"q": "是否披露了新的风险因素", "company": "蓝海能源", "kind": "boolean", "expect": True},
    {"q": "首席执行官（CEO）是谁", "company": "星辰科技", "kind": "name", "expect": "陈志远"},
    {"q": "首席财务官（CFO）是谁", "company": "蓝海能源", "kind": "name", "expect": "林晓彤"},
    {"q": "新任命了哪些高管", "company": "星辰科技", "kind": "names", "expect": ["王磊", "赵敏"]},
    {"q": "哪家公司2024年的研发投入更高", "company": "comparative", "kind": "comparative", "expect": "蓝海能源"},
    {"q": "哪家公司2024年的营业收入更高", "company": "comparative", "kind": "comparative", "expect": "恒宇银行"},
    {"q": "量子跳动", "company": None, "kind": "na", "expect": None},
]

TRUE_WORDS = {"true", "yes", "是", "提及", "宣布", "披露", "有", "正确", "存在"}


def norm_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("true", "yes"):
        return True
    if s in ("false", "no"):
        return False
    if any(w in s for w in TRUE_WORDS):
        return True
    if any(w in s for w in ("否", "未提及", "没有", "不存在", "false")):
        return False
    return None


def check(gold, ans):
    """返回 (是否通过, 实际值摘要)。"""
    v = ans.get("value")
    if gold["kind"] == "na":
        refused = v is None or str(v).strip().lower() in ("n/a", "na", "none", "")
        return refused, f"value={v!r}"
    if v is None:
        return False, "value=None（未作答）"
    if gold["kind"] == "number":
        nums = re.findall(r"-?\d+\.?\d*", str(v))
        if not nums:
            return False, f"无法从 {v!r} 提取数值"
        x = float(nums[0])
        e = gold["expect"]
        # 占比题：0.62 与 62 等价
        ok = abs(x - e) <= 0.05 or (gold.get("pct") and abs(x * 100 - e) <= 0.5)
        return ok, f"提取值={x} 期望值={e}"
    if gold["kind"] == "boolean":
        b = norm_bool(v)
        return b is gold["expect"], f"归一化={b} 期望={gold['expect']} 原始={v!r}"
    if gold["kind"] == "name":
        return gold["expect"] in str(v), f"期望 {gold['expect']} 包含于 {v!r}"
    if gold["kind"] == "names":
        missing = [n for n in gold["expect"] if n not in str(v)]
        return not missing, f"缺失={missing} 原始={v!r}"
    if gold["kind"] == "comparative":
        return gold["expect"] in str(v), f"期望 {gold['expect']} 原始={v!r}"
    return False, "未知题型"


def main():
    answers_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if answers_path is None:
        candidates = sorted(MY_SET.glob("answers_max_nst_o3m_0*.json"))
        answers_path = candidates[-1]
    data = json.load(io.open(answers_path, encoding="utf-8"))
    answers = data.get("questions") or data.get("answers") or []
    print(f"评测文件: {answers_path.name}  题目数: {len(answers)}")

    rows, by_kind = [], {}
    ref_ok, ref_total = 0, 0
    for gold, ans in zip(GOLD, answers):
        ok, detail = check(gold, ans)
        refs = ans.get("references") or []
        if gold["kind"] != "na":
            ref_total += 1
            if refs:
                ref_ok += 1
        by_kind.setdefault(gold["kind"], [0, 0])
        by_kind[gold["kind"]][1] += 1
        by_kind[gold["kind"]][0] += int(ok)
        rows.append({
            "question": ans.get("question_text", gold["q"]),
            "kind": gold["kind"], "ok": ok,
            "value": ans.get("value"), "detail": detail,
            "refs": len(refs),
        })
        mark = "✅" if ok else "❌"
        print(f"{mark} [{gold['kind']:>11}] {ans.get('question_text','')[:38]}  {detail}  refs={len(refs)}")

    total_ok = sum(r["ok"] for r in rows)
    print(f"\n总准确率: {total_ok}/{len(rows)} = {total_ok/len(rows)*100:.1f}%")
    for k, (ok, n) in by_kind.items():
        print(f"  {k:<11} {ok}/{n} = {ok/n*100:.0f}%")
    print(f"引用合规率: {ref_ok}/{ref_total} = {ref_ok/ref_total*100:.0f}%")

    out = {
        "answers_file": answers_path.name,
        "total": len(rows), "correct": total_ok,
        "accuracy": round(total_ok / len(rows), 4),
        "by_kind": {k: {"correct": v[0], "total": v[1]} for k, v in by_kind.items()},
        "reference_compliance": f"{ref_ok}/{ref_total}",
        "rows": rows,
    }
    report_json = MY_SET / "eval_result.json"
    report_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n明细已保存: {report_json}")

if __name__ == "__main__":
    main()
