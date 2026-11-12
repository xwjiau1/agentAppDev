# Harness技能目录与按需加载

## 技术实现

SkillLoader扫描技能元信息，系统提示先暴露名称和简要描述，只有请求具体技能时才返回正文。

## 应用思路

将较大的规则和操作资料按需加载，减少初始提示词体积，并保留资源目录供读取。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 摘要目录

[s07_skill_loading/code.py，115–121行](../../应用侧/自动化与工具助手/通用AgentHarness/s07_skill_loading/code.py#L115-L121)

```python
def catalog(self) -> str:
    if not self.skills:
        return "(no skills found)"
    return "\n".join(
        f"- {skill['name']}: {skill['description']}"
        for skill in self.skills.values()
    )
```

目录只列name与description，不把每份正文都放进系统提示。

### 按名称加载正文

[s07_skill_loading/code.py，123–128行](../../应用侧/自动化与工具助手/通用AgentHarness/s07_skill_loading/code.py#L123-L128)

```python
def load(self, name: str) -> str:
    skill = self.skills.get(name)
    if skill:
        return skill["content"]
    available = ", ".join(self.skills) or "none"
    return f"Error: Unknown skill '{name}'. Available: {available}"
```

从扫描后的映射中查找正文，不存在时返回可用名称，避免任意路径读取。

## 实现差异与边界

技能资料本身是外部内容，加载不等于它能覆盖宿主权限。仓库skills文件保留供参考，本次整理没有执行。
