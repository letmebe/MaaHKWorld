"""
自定义识别器 - 检查播种图像
"""
import json
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.define import RectType
from logger import log


class CheckPlantingImage(CustomRecognition):
    """
    检查播种图像识别器
    
    使用模板匹配识别播种图标
    """
    
    def __init__(self):
        super().__init__()
    
    def analyze(self, context: Context, argv) -> RectType:
        """
        执行播种图像识别
        
        Args:
            argv.custom_recognition_param: 参数
                - roi: ROI区域 [x, y, w, h]
                - template_name: 模板名称
                - threshold: 匹配阈值
        
        Returns:
            RectType: 命中返回box，未命中返回None
        """
        from maa.pipeline import JRecognitionType, JTemplateMatch
        
        # 解析参数
        param = argv.custom_recognition_param
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        # 获取参数
        roi = param.get('roi', [1750, 950, 170, 130])
        template_name = param.get('template_name', 'bozhongyaocai.png')
        threshold = param.get('threshold', 0.7)
        
        log(f"[CheckPlantingImage] 开始识别")
        log(f"[CheckPlantingImage] 参数: roi={roi}, template={template_name}, threshold={threshold}")
        
        # 获取图像
        image = argv.image
        if image is None:
            log(f"[CheckPlantingImage] ❌ image为None")
            return None
        
        log(f"[CheckPlantingImage] 图像尺寸: {image.shape}")
        
        try:
            # 构造模板匹配参数
            from maa.pipeline import JTemplateMatch
            template_param = JTemplateMatch(
                roi=roi,
                template=[template_name],  # template是字符串列表
                threshold=[threshold]      # threshold也是列表
            )
            
            log(f"[CheckPlantingImage] JTemplateMatch构造成功")
            log(f"[CheckPlantingImage] 调用原生TemplateMatch...")
            
            # 调用原生模板匹配
            result = context.run_recognition_direct(
                reco_type=JRecognitionType.TemplateMatch,
                reco_param=template_param,
                image=image
            )
            
            log(f"[CheckPlantingImage] 识别结果: {result}")
            
            if result:
                log(f"[CheckPlantingImage] best_result: {result.best_result}")
                if result.all_results:
                    log(f"[CheckPlantingImage] all_results数量: {len(result.all_results)}")
                    for i, r in enumerate(result.all_results):
                        log(f"[CheckPlantingImage] all_results[{i}]: {r}")
            
            if result and result.best_result:
                box = result.best_result.box
                score = result.best_result.score if hasattr(result.best_result, 'score') else 0
                log(f"[CheckPlantingImage] ✓ 命中! box={box}, score={score:.4f}")
                return box
            else:
                log(f"[CheckPlantingImage] ✗ 未命中")
                return None
                
        except Exception as e:
            log(f"[CheckPlantingImage] ❌ 异常: {e}")
            import traceback
            log(f"[CheckPlantingImage] 异常堆栈:\n{traceback.format_exc()}")
            return None