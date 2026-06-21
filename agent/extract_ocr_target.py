"""
自定义动作 - 提取OCR目标位置
从OCR识别结果中提取目标位置，存储到context供后续使用
"""
import json
from maa.custom_action import CustomAction
from maa.context import Context
from logger import log


class ExtractOCRTarget(CustomAction):
    """提取OCR识别结果中的目标位置"""
    
    def run(self, context: Context, argv) -> bool:
        # 获取识别结果
        reco_detail = argv.reco_detail
        if not reco_detail:
            log("[ExtractOCRTarget] 无识别结果")
            return False
        
        # 从raw_detail获取OCR结果
        detail_dict = reco_detail.raw_detail
        if not detail_dict:
            log("[ExtractOCRTarget] 无识别detail")
            return False
        
        best = detail_dict.get('best', {})
        box = best.get('box', [])
        
        if not box or len(box) < 4:
            log("[ExtractOCRTarget] 无box")
            return False
        
        # OCR box格式：[x, y, w, h]
        x, y, w, h = box[0], box[1], box[2], box[3]
        target_x = x + w // 2
        target_y = y + h // 2
        
        # 获取识别的文本
        text = best.get('text', '未知')
        
        log(f"[ExtractOCRTarget] 提取目标位置: ({target_x}, {target_y}), 文本: {text}")
        
        # 解析参数
        param = argv.custom_action_param
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        next_task = param.get('next_task')
        next_tasks = param.get('next_tasks', [])
        
        if not next_task and not next_tasks:
            log("[ExtractOCRTarget] 错误：未设置next_task或next_tasks参数！请在配置中明确指定")
            return False
        
        tolerance = param.get('tolerance', 10)
        max_iterations = param.get('max_iterations', 20)
        
        move_param = json.dumps({
            "target_x": target_x,
            "target_y": target_y,
            "tolerance": tolerance,
            "max_iterations": max_iterations,
            "stick": "left"
        })
        
        near_target_param = json.dumps({
            "target_x": target_x,
            "target_y": target_y,
            "tolerance": tolerance,
        })
        
        override_data = {}
        
        if next_task:
            override_data[next_task] = {
                "custom_action_param": move_param
            }
            log(f"[ExtractOCRTarget] 已设置下一个任务参数: {next_task}")
        
        for task_name, task_type in next_tasks:
            if task_type == "move":
                override_data[task_name] = {
                    "custom_action_param": move_param
                }
            elif task_type == "near_target":
                override_data[task_name] = {
                    "custom_recognition_param": near_target_param
                }
            log(f"[ExtractOCRTarget] 已设置任务参数: {task_name} (类型: {task_type})")
        
        context.override_pipeline(override_data)
        
        return True