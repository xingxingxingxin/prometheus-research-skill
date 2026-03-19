# User Skills Directory
#
# 用户自定义技能可以放在这个目录下
# 每个技能文件应该定义一个继承自 Core.skills.base.Skill 的类
#
# 示例:
#
# from Core.skills.base import DeterministicSkill, SkillContext, SkillResult
#
# class MyCustomSkill(DeterministicSkill):
#     name = "my_custom_skill"
#     description = "My custom skill"
#     inputs = ["input_data"]
#     outputs = ["output_data"]
#
#     def execute(self, context: SkillContext) -> SkillResult:
#         # 实现你的技能逻辑
#         return SkillResult(success=True, outputs={"output_data": result})
