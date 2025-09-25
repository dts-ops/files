import os, sys, time, random, threading
import numpy as np
import pysrt
import sounddevice as sd
from colorama import init, Fore
from pydub import AudioSegment

# Khởi tạo
init(autoreset=True)
WIDTH = os.get_terminal_size().columns
blocks = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
COLOR = [Fore.RED, Fore.GREEN, Fore.BLUE, Fore.YELLOW, Fore.CYAN, Fore.MAGENTA, Fore.WHITE]

# ==== File audio & subs ====
audio_path = "nnhp.wav"
subs = pysrt.open("nnhp.srt")
duration = int(AudioSegment.from_file(audio_path).duration_seconds)

# Flag để dừng thread
stop_event = threading.Event()

# ====== Hàm phụ ======
def srt_time_to_seconds(srt_time):
    return (srt_time.hours*3600 + srt_time.minutes*60 +
            srt_time.seconds + srt_time.milliseconds/1000)

def autocl(text):
    return random.choice(COLOR) + text.center(WIDTH)

# ====== Wave visualizer ======
def wave_ms():
    while not stop_event.is_set():
        layer = "".join(random.choice(blocks) for _ in range(24)).center(WIDTH)
        layer = Fore.CYAN + layer
        sys.stdout.write("\033[4;1H\033[2K" + layer)
        sys.stdout.flush()
        time.sleep(0.1)

# ====== Timeline ======
def dot_timeline(total_seconds, line_length=40):
    for elapsed in range(total_seconds + 1):
        if stop_event.is_set(): break
        pos = int(line_length * elapsed / total_seconds)
        line_plain = "".join("─" if i < pos else "■" if i == pos else "-" 
                             for i in range(line_length))
        mins, secs = divmod(elapsed, 60)
        _mins, _secs = divmod(total_seconds, 60)
        padded = f"|{line_plain}| {mins:02d}:{secs:02d}/{_mins:02d}:{_secs:02d}".center(WIDTH)

        colored = "".join(
            Fore.BLUE + "■" if ch == "■" else
            Fore.WHITE + "-" if ch == "-" else
            Fore.BLUE + ch
            for ch in padded
        )
        sys.stdout.write("\033[7;1H\033[2K" + colored)
        sys.stdout.flush()
        time.sleep(1)

# ====== Lyrics ======
def sub_handle(subs):
    print("\n"*15)
    start_time = time.time()
    for sub in subs:
        t_start = srt_time_to_seconds(sub.start)
        t_end = srt_time_to_seconds(sub.end)

        while time.time() - start_time < t_start:
            if stop_event.is_set(): return
            time.sleep(0.01)

        text = sub.text.strip().replace("\n", " ")
        sys.stdout.write("\033[6;1H\033[2K" + autocl(text)[:WIDTH].center(WIDTH))
        sys.stdout.flush()

        while time.time() - start_time < t_end:
            if stop_event.is_set(): return
            time.sleep(0.01)

# ====== Play sound ======
def play_sound(path):
    song = AudioSegment.from_file(path)
    samples = np.array(song.get_array_of_samples())
    if song.channels == 2:
        samples = samples.reshape(-1, 2).mean(axis=1).astype(np.int16)
    else:
        samples = samples.astype(np.int16)
    sd.play(samples, song.frame_rate)
    sd.wait()
    stop_event.set()

# ====== Main ======
threads = [
    threading.Thread(target=sub_handle, args=(subs,)),
    threading.Thread(target=wave_ms),
    threading.Thread(target=dot_timeline, args=(duration,)),
    threading.Thread(target=play_sound, args=(audio_path,))
]

for t in threads: t.start()
for t in threads: t.join()
