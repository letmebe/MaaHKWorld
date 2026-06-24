"""
自定义动作和识别器 - 探险派遣循环控制器
"""
import json
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.define import Rect

from utils.logger import log


class DispatchLoopController(CustomAction):
    """
    探险派遣循环控制器（单例模式）
    
    从interface.json的option读取配置，动态控制循环流程
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            # 初始化属性，避免AttributeError
            instance.locations = []
            instance.persons = {}
            instance.current_location_index = 0
            instance.current_person_index = 0
            instance.initialized = False
            cls._instance = instance
        return cls._instance
    
    def run(self, context: Context, argv) -> bool:
        """
        执行循环控制
        
        Args:
            argv.custom_action_param: {"action": "init" | "next_location" | "next_person"}
        
        Returns:
            bool: True继续循环，False停止
        """
        # 解析参数（处理多重JSON编码和嵌套JSON字符串）
        param = argv.custom_action_param
        log(f"[DispatchLoop] run 收到的原始param: {param}, 类型: {type(param)}")
        
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
                
                # 处理嵌套的JSON字符串（如config字段）
                if isinstance(param, dict):
                    for key, value in param.items():
                        if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                            try:
                                param[key] = json.loads(value)
                            except:
                                pass
            except Exception as e:
                log(f"[DispatchLoop] JSON解析异常: {e}")
                param = {}
        
        log(f"[DispatchLoop] 解析后的param: {param}")
        action = param.get('action', 'init')
        
        if action == 'init':
            config_str = param.get('config')
            return self._init_config(context, config_str)
        elif action == 'next_location':
            return self._next_location(context)
        elif action == 'next_person':
            return self._next_person(context)
        else:
            log(f"[DispatchLoop] 未知动作: {action}")
            return False
    
    def _init_config(self, context: Context, config_str: str = None) -> bool:
        """初始化配置（每次任务开始都重置状态）"""
        log(f"[DispatchLoop] _init_config 收到的config_str: {config_str}, 类型: {type(config_str)}")
        
        # 重置状态（支持多次运行）
        self.locations = []
        self.persons = {}
        self.current_location_index = 0
        self.current_person_index = 0
        self.initialized = False
        
        # 如果没有提供配置，使用默认配置
        if not config_str:
            config_str = '{"locations": ["春溪原", "秘禁之地", "稷下学院"], "persons": {"春溪原": ["阿噗", "啾啾", "哆哆"], "秘禁之地": ["卫宁", "堂听虎", "小红"], "稷下学院": ["学典鹅", "酷酷", "聪聪"]}}'
            log(f"[DispatchLoop] 未提供配置，使用默认配置")
        
        try:
            # 支持dict或JSON字符串输入
            if isinstance(config_str, dict):
                config = config_str
            else:
                config = json.loads(config_str)
            
            self.locations = config.get('locations', [])
            self.persons = config.get('persons', {})
            
            log(f"[DispatchLoop] 配置初始化成功")
            log(f"[DispatchLoop] 地点: {self.locations}")
            log(f"[DispatchLoop] 人员: {self.persons}")
            
            self.initialized = True
            return True
        except Exception as e:
            log(f"[DispatchLoop] 配置解析失败: {e}")
            return False
    
    def _next_location(self, context: Context) -> bool:
        """切换到下一个地点"""
        log(f"[DispatchLoop] _next_location 开始执行")
        log(f"[DispatchLoop] initialized={self.initialized}, current_location_index={self.current_location_index}, len(locations)={len(self.locations)}")
        
        if not self.initialized:
            if not self._init_config(context, None):
                log(f"[DispatchLoop] _next_location 初始化失败，返回False")
                return False
        
        # 注意location_index的自增在_next_Person中处理,加到len(self.locations)后CheckLocationCount跳出，就不会再进入_next_location了
       
        location = self.locations[self.current_location_index]
        persons = self.persons.get(location, [])
        
        log(f"[DispatchLoop] 处理地点 {self.current_location_index + 1}/{len(self.locations)}: {location}")
        log(f"[DispatchLoop] 人员列表: {persons}")
        
        # 重置人员索引
        self.current_person_index = 0
        
        # 动态override pipeline（只修改地点识别参数）
        context.override_pipeline({
            "探险派遣循环版_查找地点": {
                "recognition": {
                    "type": "OCR",
                    "param": {
                        "roi": [380, 0, 1060, 1080],
                        "expected": [location]
                    }
                }
            }
        })
       
        return True
    
    def _next_person(self, context: Context) -> bool:
        """切换到下一个人员"""
        if not self.initialized:
            if not self._init_config(context, None):
                return False
        
        location = self.locations[self.current_location_index]
        persons = self.persons.get(location, [])
        

        person = persons[self.current_person_index]
        
        log(f"[DispatchLoop] 处理人员 {self.current_person_index + 1}/{len(persons)}: {person}")
        
        # 动态override pipeline（只修改识别参数）
        context.override_pipeline({
            "探险派遣循环版_查找人员": {
                "recognition": {
                    "type": "OCR",
                    "param": {
                        "roi": [1290, 0, 630, 1080],
                        "expected": [person]
                    }
                }
            }
        })
        
        # 如果没有到人员列表末尾，才递增人员索引
        if self.current_person_index < len(persons):
            self.current_person_index += 1
            
        if self.current_person_index == len(persons):
            log(f"[DispatchLoop] 地点 {location} 的所有人员已派遣完成")
            # 人员遍历完，递增地点索引
            self.current_location_index += 1
        
        return True


class CheckLocationCount(CustomRecognition):
    """
    检查地点是否遍历完
    
    如果所有地点已遍历完，返回有效坐标让节点命中
    """
    
    def analyze(self, context: Context, argv):
        """
        分析地点遍历状态
        
        Returns:
            tuple: (x, y, w, h) 如果遍历完，否则返回None
        """
        controller = DispatchLoopController()
        
        if not controller.initialized:
            log("[CheckLocationCount] 控制器未初始化")
            return None
        
        if controller.current_location_index == len(controller.locations):
            log(f"[CheckLocationCount] 所有地点已遍历完 ({controller.current_location_index}/{len(controller.locations)})，返回命中")
            # 返回有效box，让节点命中
            return (960, 540, 100, 100)
        else:
            location = controller.locations[controller.current_location_index]
            log(f"[CheckLocationCount] 地点正在遍历 ({controller.current_location_index + 1}/{len(controller.locations)})，返回未命中")
            return None


class CheckPersonCount(CustomRecognition):
    """
    检查人员是否遍历完
    
    如果当前地点的所有人员已遍历完，返回有效坐标让节点命中
    """
    
    def analyze(self, context: Context, argv):
        """
        分析人员遍历状态
        
        Returns:
            tuple: (x, y, w, h) 如果遍历完，否则返回None
        """
        controller = DispatchLoopController()
        
        if not controller.initialized:
            log("[CheckPersonCount] 控制器未初始化")
            return None

        # 这段其实就为了取一个len(persons)常量    
        location = controller.locations[controller.current_location_index]
        persons = controller.persons.get(location, [])


        # 检查人员是否遍历完
        if controller.current_person_index != len(persons):
            log(f"[CheckPersonCount] 地点 {location} 的人员正在遍历 ({controller.current_person_index + 1}/{len(persons)})，返回未命中")
            return None           
        else:           
             # 注意此时controller.current_location_index已经加一，需要减一才是之前的地点
            location = controller.locations[controller.current_location_index - 1]
            log(f"[CheckPersonCount] 地点 {location} 的所有人员已遍历完 ({controller.current_person_index}/{len(persons)})，返回命中")
            # 返回有效box，让节点命中
            return (960, 540, 100, 100)