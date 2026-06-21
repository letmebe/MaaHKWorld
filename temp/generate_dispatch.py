import json

# 定义地点和人员
locations = {
    "春溪原": ["阿噗", "啾啾", "哆哆"],
    "秘禁之地": ["卫宁", "堂听虎", "小红"],
    "稷下学院": ["学典鹅", "酷酷", "聪聪"]
}

data = {}

# 开始节点
data["探险派遣_开始"] = {
    "recognition": "DirectHit",
    "action": "DoNothing",
    "next": ["探险派遣_传送到派遣小屋"]
}

# 传送到派遣小屋
data["探险派遣_传送到派遣小屋"] = {
    "recognition": "DirectHit",
    "action": "DoNothing",
    "pipeline_override": {
        "通用_传送_查找目标位置": {
            "recognition": {"type": "OCR", "param": {"expected": ["派遣小屋"]}}
        }
    },
    "next": ["通用_传送到目标"]
}

# 传送完成等待
data["探险派遣_传送完成等待"] = {
    "recognition": "DirectHit",
    "action": "DoNothing",
    "pre_delay": 2000,
    "post_wait_freezes": 1000,
    "next": ["探险派遣_向前移动"]
}

# 向前移动
data["探险派遣_向前移动"] = {
    "recognition": "DirectHit",
    "action": "Custom",
    "custom_action": "MoveStickOnce",
    "custom_action_param": json.dumps({"stick": "left", "x": 30000, "y": 10000, "duration": 0.1}),
    "post_delay": 500,
    "next": ["探险派遣_打开派遣画面"]
}

# 打开派遣画面
data["探险派遣_打开派遣画面"] = {
    "recognition": "DirectHit",
    "action": "Custom",
    "custom_action": "TapButton",
    "custom_action_param": json.dumps({"button": "Y"}),
    "post_delay": 1000,
    "next": ["探险派遣_晃动准星"]
}

# 晃动准星
data["探险派遣_晃动准星"] = {
    "recognition": "DirectHit",
    "action": "Custom",
    "custom_action": "WiggleStick",
    "custom_action_param": json.dumps({"stick_value": 10000, "duration": 0.1}),
    "post_delay": 500,
    "next": ["探险派遣_查找地点_春溪原"]
}

# 为每个地点生成流程
location_names = list(locations.keys())
for loc_idx, (location, persons) in enumerate(locations.items()):
    # 查找地点
    data[f"探险派遣_查找地点_{location}"] = {
        "recognition": {
            "type": "OCR",
            "param": {
                "roi": [380, 0, 1060, 1080],
                "expected": [location]
            }
        },
        "action": "Custom",
        "custom_action": "ExtractOCRTarget",
        "custom_action_param": json.dumps({
            "next_task": f"探险派遣_移动准星到地点_{location}",
            "tolerance": 10,
            "max_iterations": 20
        }),
        "post_delay": 500,
        "next": [f"探险派遣_移动准星到地点_{location}"]
    }
    
    # 移动准星到地点
    data[f"探险派遣_移动准星到地点_{location}"] = {
        "recognition": "Custom",
        "custom_recognition": "FindCrosshair",
        "custom_recognition_param": json.dumps({"threshold": 0.8}),
        "action": "Custom",
        "custom_action": "MoveStick",
        "custom_action_param": "{}",
        "next": [f"探险派遣_点击地点_{location}"],
        "on_error": [f"探险派遣_移动准星到地点_{location}"]
    }
    
    # 点击地点
    data[f"探险派遣_点击地点_{location}"] = {
        "recognition": "DirectHit",
        "action": "Custom",
        "custom_action": "TapButton",
        "custom_action_param": json.dumps({"button": "X"}),
        "post_delay": 500,
        "next": ["探险派遣_移动准星到菜单顶部"]
    }
    
    # 移动准星到菜单顶部（所有地点共用）
    if loc_idx == 0:
        data["探险派遣_移动准星到菜单顶部"] = {
            "recognition": "DirectHit",
            "action": "Custom",
            "custom_action": "MoveToPosition",
            "custom_action_param": json.dumps({"target_x": 1600, "target_y": 60}),
            "post_delay": 300,
            "next": [f"探险派遣_查找人员_{persons[0]}"]
        }
    
    # 为每个人员生成流程
    for person_idx, person in enumerate(persons):
        # 查找人员
        next_action = f"探险派遣_选择人员_{person}" if person_idx == len(persons) - 1 else f"探险派遣_查找人员_{persons[person_idx + 1]}"
        
        data[f"探险派遣_查找人员_{person}"] = {
            "recognition": {
                "type": "OCR",
                "param": {
                    "roi": [1290, 0, 630, 1080],
                    "expected": [person]
                }
            },
            "action": "Custom",
            "custom_action": "ExtractOCRTarget",
            "custom_action_param": json.dumps({
                "next_task": f"探险派遣_移动准星到人员_{person}",
                "tolerance": 10,
                "max_iterations": 20
            }),
            "post_delay": 300,
            "next": [f"探险派遣_移动准星到人员_{person}"],
            "on_error": [f"探险派遣_滚动菜单_{person}"]
        }
        
        # 滚动菜单
        data[f"探险派遣_滚动菜单_{person}"] = {
            "recognition": "DirectHit",
            "action": "Custom",
            "custom_action": "MoveStickOnce",
            "custom_action_param": json.dumps({"stick": "right", "x": 30000, "y": 10000, "duration": 0.1}),
            "post_delay": 300,
            "next": [f"探险派遣_查找人员_{person}"]
        }
        
        # 移动准星到人员
        data[f"探险派遣_移动准星到人员_{person}"] = {
            "recognition": "Custom",
            "custom_recognition": "FindCrosshair",
            "custom_recognition_param": json.dumps({"threshold": 0.8}),
            "action": "Custom",
            "custom_action": "MoveStick",
            "custom_action_param": "{}",
            "next": [f"探险派遣_选择人员_{person}"],
            "on_error": [f"探险派遣_移动准星到人员_{person}"]
        }
        
        # 选择人员
        if person_idx < len(persons) - 1:
            # 不是最后一个人员，继续找下一个
            data[f"探险派遣_选择人员_{person}"] = {
                "recognition": "DirectHit",
                "action": "Custom",
                "custom_action": "TapButton",
                "custom_action_param": json.dumps({"button": "A"}),
                "post_delay": 300,
                "next": [f"探险派遣_查找人员_{persons[person_idx + 1]}"]
            }
        else:
            # 最后一个人员，确认派遣
            next_location_idx = loc_idx + 1
            if next_location_idx < len(location_names):
                next_location = location_names[next_location_idx]
                data[f"探险派遣_选择人员_{person}"] = {
                    "recognition": "DirectHit",
                    "action": "Custom",
                    "custom_action": "TapButton",
                    "custom_action_param": json.dumps({"button": "A"}),
                    "post_delay": 300,
                    "next": [f"探险派遣_确认派遣_{location}"]
                }
            else:
                # 最后一个地点的最后一个人
                data[f"探险派遣_选择人员_{person}"] = {
                    "recognition": "DirectHit",
                    "action": "Custom",
                    "custom_action": "TapButton",
                    "custom_action_param": json.dumps({"button": "A"}),
                    "post_delay": 300,
                    "next": [f"探险派遣_确认派遣_{location}"]
                }
    
    # 确认派遣
    next_location_idx = loc_idx + 1
    if next_location_idx < len(location_names):
        next_location = location_names[next_location_idx]
        data[f"探险派遣_确认派遣_{location}"] = {
            "recognition": "DirectHit",
            "action": "Custom",
            "custom_action": "TapButton",
            "custom_action_param": json.dumps({"button": "X"}),
            "post_delay": 500,
            "next": [f"探险派遣_查找地点_{next_location}"]
        }
    else:
        # 最后一个地点，退出派遣画面
        data[f"探险派遣_确认派遣_{location}"] = {
            "recognition": "DirectHit",
            "action": "Custom",
            "custom_action": "TapButton",
            "custom_action_param": json.dumps({"button": "X"}),
            "post_delay": 500,
            "next": ["探险派遣_退出派遣画面"]
        }

# 退出派遣画面
data["探险派遣_退出派遣画面"] = {
    "recognition": "DirectHit",
    "action": "Custom",
    "custom_action": "TapButton",
    "custom_action_param": json.dumps({"button": "B"}),
    "post_delay": 1000
}

# 保存
with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'完成！共生成 {len(data)} 个节点')