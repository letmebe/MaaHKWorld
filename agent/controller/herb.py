"""
自定义识别器和动作 - 药草种植控制器
"""
import json
import re
import os
from datetime import datetime, timedelta
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
from maa.context import Context
from utils.logger import log


class HerbPlantController:
    """
    药草种植控制器（单例模式）
    
    管理种植计数和浇水时间间隔
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.plant_count = 0
            instance.watering_interval_hours = 0
            instance.initialized = False
            cls._instance = instance
        return cls._instance
    
    def reset(self):
        """重置状态"""
        self.plant_count = 0
        self.watering_interval_hours = 0
        self.initialized = True
        log(f"[HerbPlant] 状态重置")
    
    def increment_count(self):
        """增加种植计数"""
        self.plant_count += 1
        log(f"[HerbPlant] 种植计数: {self.plant_count}")
    
    def set_watering_interval(self, hours):
        """设置浇水时间间隔"""
        self.watering_interval_hours = hours
        log(f"[HerbPlant] 浇水间隔: {hours}小时")
    
    def save_next_watering_time(self):
        """保存下次浇水时间到文件"""
        next_time = datetime.now() + timedelta(hours=self.watering_interval_hours)
        time_str = next_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存到文件
        file_path = os.path.join(os.path.dirname(__file__), "..", "herb_watering_time.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(time_str)
        
        log(f"[HerbPlant] 下次浇水时间已保存: {time_str}")


class CheckPlantCount(CustomRecognition):
    """
    检查种植计数是否超过阈值
    
    如果计数 >= threshold，返回命中
    """
    
    def __init__(self):
        super().__init__()
    
    def analyze(self, context: Context, argv):
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
        
        threshold = param.get('threshold', 10)
        
        controller = HerbPlantController()
        
        if controller.plant_count >= threshold:
            log(f"[CheckPlantCount] 种植计数已达阈值: {controller.plant_count}/{threshold}，返回命中")
            return (960, 540, 100, 100)
        else:
            log(f"[CheckPlantCount] 种植计数未达阈值: {controller.plant_count}/{threshold}，返回未命中")
            return None


class IncrementPlantCount(CustomAction):
    """
    增加种植计数
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        controller = HerbPlantController()
        controller.increment_count()
        return True


class ParseWateringTime(CustomAction):
    """
    解析浇水时间文本并记录
    
    从OCR识别结果中提取时间信息，格式如"12小时30分"
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        # 获取OCR识别结果
        reco_detail = argv.reco_detail
        if not reco_detail:
            log("[ParseWateringTime] 无识别结果")
            return False
        
        detail_dict = reco_detail.raw_detail
        if not detail_dict:
            log("[ParseWateringTime] 无识别detail")
            return False
        
        best = detail_dict.get('best', {})
        text = best.get('text', '')
        
        if not text:
            log("[ParseWateringTime] 无文本")
            return False
        
        log(f"[ParseWateringTime] 识别文本: {text}")
        
        # 解析时间格式：如"12小时30分"或"12:30"
        hours = 0
        minutes = 0
        
        # 尝试匹配"X小时Y分"格式
        match = re.search(r'(\d+)\s*小时\s*(\d+)\s*分', text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
        else:
            # 尝试匹配"X小时"格式
            match = re.search(r'(\d+)\s*小时', text)
            if match:
                hours = int(match.group(1))
            else:
                # 尝试匹配"X:Y"格式
                match = re.search(r'(\d+)\s*:\s*(\d+)', text)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
        
        if hours > 0 or minutes > 0:
            total_hours = hours + minutes / 60.0
            controller = HerbPlantController()
            controller.set_watering_interval(total_hours)
            log(f"[ParseWateringTime] 解析成功: {hours}小时{minutes}分 = {total_hours}小时")
            return True
        else:
            log(f"[ParseWateringTime] 未识别到时间格式")
            return False


class SaveWateringTime(CustomAction):
    """
    保存下次浇水时间到文件
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        controller = HerbPlantController()
        controller.save_next_watering_time()
        return True


class ResetHerbPlant(CustomAction):
    """
    重置药草种植状态
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        controller = HerbPlantController()
        controller.reset()
        return True


class CheckTilledField(CustomRecognition):
    """
    检查是否显示"需要在已开垦田地上播种"文本
    
    始终返回命中，在detail中记录是否真的识别到文本
    """
    
    def __init__(self):
        super().__init__()
    
    def analyze(self, context: Context, argv):
        from maa.pipeline import JRecognitionType, JOCR
        
        # 从参数中提取roi
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
        
        roi = param.get('roi', [400, 400, 1120, 280])
        
        image = argv.image
        if image is None:
            return CustomRecognition.AnalyzeResult(
                box=(960, 540, 100, 100),
                detail=json.dumps({'texts': []})
            )
        
        # 使用context.run_recognition_direct执行OCR，不使用expected过滤
        ocr_param = JOCR(roi=roi)
        
        result = context.run_recognition_direct(
            reco_type=JRecognitionType.OCR,
            reco_param=ocr_param,
            image=image
        )
        
        # 收集所有识别到的文本
        texts = []
        if result and result.all_results:
            for r in result.all_results:
                ocr_text = r.text if hasattr(r, 'text') else ''
                if ocr_text:
                    texts.append(ocr_text)
        
        log(f"[CheckTilledField] OCR识别(roi={roi}): 识别到{len(texts)}个文本: {texts}")
        
        # 始终返回命中，detail包含所有识别到的文本
        return CustomRecognition.AnalyzeResult(
            box=(960, 540, 100, 100),
            detail=json.dumps({'texts': texts})
        )



class IncrementPlantCountIfHit(CustomAction):
    """
    根据识别到的文本更新种植计数
    
    - 未识别到文本：啥也不做
    - 识别到"需要在已开垦田地上播种"：次数加一
    - 识别到其他文本：次数清零
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        reco_detail = argv.reco_detail
        if not reco_detail:
            log("[IncrementPlantCountIfHit] 无reco_detail")
            return True
        
        detail_dict = reco_detail.raw_detail
        if not detail_dict:
            log("[IncrementPlantCountIfHit] 无detail_dict")
            return True
        
        best = detail_dict.get('best', {})
        detail = best.get('detail', {})
        
        # detail可能是字符串，需要双重解析
        if isinstance(detail, str):
            try:
                parsed = json.loads(detail)
                if isinstance(parsed, str):
                    detail = json.loads(parsed)
                else:
                    detail = parsed
            except:
                detail = {}
        
        texts = detail.get('texts', [])
        controller = HerbPlantController()
        
        if not texts:
            # 未识别到文本，啥也不做
            log(f"[IncrementPlantCountIfHit] 未识别到文本，保持计数: {controller.plant_count}")
        elif any("需要在已开垦田地上播种" in t for t in texts):
            # 识别到目标文本，次数加一
            controller.increment_count()
        else:
            # 识别到其他文本，次数清零
            controller.plant_count = 0
            log(f"[IncrementPlantCountIfHit] 识别到其他文本{texts}，计数清零")
        
        return True


class CheckWateringTimeText(CustomRecognition):
    """
    检查是否显示浇水时间文本
    
    始终返回命中，在detail中记录是否真的识别到时间文本
    """
    
    def __init__(self):
        super().__init__()
    
    def analyze(self, context: Context, argv):
        from maa.pipeline import JRecognitionType, JOCR
        
        # 从参数中提取roi
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
        
        roi = param.get('roi', [1750, 950, 80, 130])
        
        image = argv.image
        if image is None:
            log(f"[CheckWateringTimeText] image为None，返回未命中")
            return CustomRecognition.AnalyzeResult(
                box=(960, 540, 100, 100),
                detail=json.dumps({'hit': False, 'text': ''})
            )
        
        # 使用context.run_recognition_direct执行OCR，不使用expected过滤
        ocr_param = JOCR(roi=roi)
        
        result = context.run_recognition_direct(
            reco_type=JRecognitionType.OCR,
            reco_param=ocr_param,
            image=image
        )
        
        log(f"[CheckWateringTimeText] OCR结果: {result}")
        if result:
            log(f"[CheckWateringTimeText] best_result: {result.best_result}")
            if result.all_results:
                log(f"[CheckWateringTimeText] all_results数量: {len(result.all_results)}")
                for i, r in enumerate(result.all_results):
                    log(f"[CheckWateringTimeText] all_results[{i}]: {r}")
        
        hit = False
        text = ''
        
        # 检查所有OCR结果中是否包含时间关键字
        if result and result.all_results:
            for r in result.all_results:
                # OCRResult的文本在text属性中
                ocr_text = r.text if hasattr(r, 'text') else ''
                if ocr_text and ('小时' in ocr_text or '分' in ocr_text):
                    hit = True
                    text = ocr_text
                    log(f"[CheckWateringTimeText] 找到时间文本: {text}")
                    break
        
        log(f"[CheckWateringTimeText] OCR识别(roi={roi}): hit={hit}, text={text}")
        
        # 始终返回命中
        return CustomRecognition.AnalyzeResult(
            box=(960, 540, 100, 100),
            detail=json.dumps({'hit': hit, 'text': text})
        )


class ParseWateringTimeIfHit(CustomAction):
    """
    如果识别到时间文本，解析并记录浇水时间
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        reco_detail = argv.reco_detail
        if not reco_detail:
            log("[ParseWateringTimeIfHit] 无reco_detail")
            return True
        
        detail_dict = reco_detail.raw_detail
        if not detail_dict:
            log("[ParseWateringTimeIfHit] 无detail_dict")
            return True
        
        best = detail_dict.get('best', {})
        detail = best.get('detail', {})
        
        log(f"[ParseWateringTimeIfHit] 原始detail: {detail}, 类型: {type(detail)}")
        
        # detail可能是字符串，需要双重解析
        if isinstance(detail, str):
            try:
                parsed = json.loads(detail)
                if isinstance(parsed, str):
                    detail = json.loads(parsed)
                else:
                    detail = parsed
                log(f"[ParseWateringTimeIfHit] 解析后的detail: {detail}, 类型: {type(detail)}")
            except:
                detail = {}
        
        hit = detail.get('hit', False)
        text = detail.get('text', '')
        
        log(f"[ParseWateringTimeIfHit] hit={hit}, text={text}")
        
        if not hit:
            log("[ParseWateringTimeIfHit] 未识别到时间文本，跳过解析")
            return True
        
        # 解析时间格式
        hours = 0
        minutes = 0
        
        match = re.search(r'(\d+)\s*小时\s*(\d+)\s*分', text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
        else:
            match = re.search(r'(\d+)\s*小时', text)
            if match:
                hours = int(match.group(1))
            else:
                match = re.search(r'(\d+)\s*:\s*(\d+)', text)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
        
        if hours > 0 or minutes > 0:
            total_hours = hours + minutes / 60.0
            controller = HerbPlantController()
            controller.set_watering_interval(total_hours)
            log(f"[ParseWateringTimeIfHit] 解析成功: {hours}小时{minutes}分 = {total_hours}小时")
        else:
            log(f"[ParseWateringTimeIfHit] 未识别到时间格式: {text}")
        
        return True
