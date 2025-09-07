# realtime_vosk_zh.py
import json, queue, sys, time
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# ===== 基本配置 =====
MODEL_PATH   = "vosk-model-small-cn-0.22"  # 修改为你的模型目录
SAMPLE_RATE  = 16000
BLOCK_BYTES  = 4000      # 每次送入识别器的字节数（~0.125s）；更小更“实时”
DEVICE_INDEX = None      # 指定麦克风设备索引；None=系统默认

print("Loading model ...")
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(True)  # 如果模型支持，将提供词级时间戳

audio_q = queue.Queue()

def audio_cb(indata, frames, t, status):
    if status:  # 欠载/超载等
        print("Audio status:", status, file=sys.stderr)
    audio_q.put(bytes(indata))  # 原始 int16 小端字节

def main():
    final_lines = []
    partial_last = ""
    print("开始说话...（Ctrl+C 结束）")

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=0,              # 让驱动自行分块，我们以队列再二次分包
        device=DEVICE_INDEX,
        dtype="int16",
        channels=1,
        callback=audio_cb
    ):
        buf = b""
        try:
            while True:
                # 聚合回调字节，按 BLOCK_BYTES 分包喂给 Vosk
                data = audio_q.get()
                buf += data
                while len(buf) >= BLOCK_BYTES:
                    chunk = buf[:BLOCK_BYTES]
                    buf = buf[BLOCK_BYTES:]

                    if rec.AcceptWaveform(chunk):
                        # 到达端点 -> 最终结果
                        res = json.loads(rec.Result())
                        text = res.get("text", "").strip()
                        if text:
                            print("\n【最终】", text)
                            final_lines.append(text)
                            partial_last = ""
                    else:
                        # 中间结果（覆盖式打印）
                        pres = json.loads(rec.PartialResult())
                        p = pres.get("partial", "").strip()
                        if p and p != partial_last:
                            print("… " + p + "     ", end="\r", flush=True)
                            partial_last = p
        except KeyboardInterrupt:
            print("\n结束，收尾中…")
            last = json.loads(rec.FinalResult()).get("text", "").strip()
            if last:
                print("【最终】", last)
                final_lines.append(last)
        finally:
            with open("transcript.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(final_lines))
            print("已写入 transcript.txt")

if __name__ == "__main__":
    main()
