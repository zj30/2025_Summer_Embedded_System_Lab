from pypinyin import pinyin, Style
from thefuzz import fuzz

# --- 预处理和缓存，提高效率 ---
# 1. 定义标准指令集
TARGET_COMMANDS = ["高速", "中速", "低速", "关闭"]

# 2. 创建一个内部缓存，避免重复计算拼音
_PINYIN_CACHE = {}

def _to_pinyin_string(text: str) -> str:
    """内部辅助函数：将汉字文本转换为连续的、无声调的拼音字符串。"""
    if not text:
        return ""
    if text in _PINYIN_CACHE:
        return _PINYIN_CACHE[text]
    
    # 将 "低速" 转换为 [[&#x27;di&#x27;], [&#x27;su&#x27;]]
    pinyin_list = pinyin(text, style=Style.NORMAL) 
    # 将 [[&#x27;di&#x27;], [&#x27;su&#x27;]] 拼接为 "disu"
    result = "".join(char[0] for char in pinyin_list)
    
    _PINYIN_CACHE[text] = result
    return result

# 3. 预先计算好所有目标指令的拼音，这样函数每次调用时无需重复计算
TARGET_COMMANDS_PINYIN = {cmd: _to_pinyin_string(cmd) for cmd in TARGET_COMMANDS}
# TARGET_COMMANDS_PINYIN 的内容会是: {&#x27;高速&#x27;: &#x27;gaosu&#x27;, &#x27;中速&#x27;: &#x27;zhongsu&#x27;, &#x27;低速&#x27;: &#x27;disu&#x27;}


def get_speed_command_match(recognized_text: str, score_cutoff: int = 70) -> tuple:
    """
    检测一个词汇与“高速”、“中速”、“低速”的语音近似度。

    该函数通过将输入词汇和目标词汇转换为无声调的拼音，
    然后使用模糊字符串匹配算法计算它们的相似度分数。

    Args:
        recognized_text (str): 语音识别返回的待检测词汇。
        score_cutoff (int, optional): 相似度得分阈值 (0-100)。
                                      只有得分高于此阈值的才被认为是有效匹配。
                                      默认为 70。

    Returns:
        tuple: 一个包含两个元素的元组 (best_match, score)。
               - best_match (str or None): 匹配到的最佳指令 ("高速", "中速", "低速")。
                                           如果没有超过阈值的匹配，则为 None。
               - score (int): 最佳匹配的相似度分数 (0-100)。
    """
    if not recognized_text:
        return (None, 0)

    # 获取输入词汇的拼音
    recognized_pinyin = _to_pinyin_string(recognized_text)
    
    best_match_command = None
    highest_score = 0

    # 遍历所有预先计算好的目标拼音
    for command, command_pinyin in TARGET_COMMANDS_PINYIN.items():
        # 计算输入词汇与每个目标词汇的拼音相似度
        score = fuzz.ratio(recognized_pinyin, command_pinyin)
        
        # 如果找到了一个分数更高的匹配，则更新记录
        if score > highest_score:
            highest_score = score
            best_match_command = command
            
    # 只有当最高分超过我们设定的阈值时，才认为匹配成功
    if highest_score >= score_cutoff:
        print(best_match_command)
        return (best_match_command, highest_score)
    else:
        # 否则，返回未匹配成功
        return (None, 0)

# --- 如何使用它：示例 ---
if __name__ == "__main__":
    # 准备一组测试词汇，包含同音、近音和无关词
    test_words = [
        "高速",    # 精确匹配
        "高数",    # 近音词
        "滴速",    # 同音词
        "泥塑",    # 同音混淆词
        "中宿",    # 近音词
        "管壁",    # 另一个同音混淆词 (对比 "关闭")
        "关闭",    # 用于对比
        "你好",    # 无关词
        ""         # 空字符串
    ]

    print("--- 开始测试语音近似度检测函数 ---\n")
    for word in test_words:
        # 调用函数进行检测
        matched_command, score = get_speed_command_match(word)
        
        print(f"输入: &#x27;{word}&#x27;")
        if matched_command:
            print(f"  ==> 匹配成功! 最佳匹配: &#x27;{matched_command}&#x27;, 语音相似度: {score}%\n")
        else:
            print(f"  ==> 匹配失败。最高相似度为 {score}%, 未达到阈值。\n")
