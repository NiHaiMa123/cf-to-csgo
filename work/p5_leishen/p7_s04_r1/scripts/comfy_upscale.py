import json, urllib.request, time, sys, shutil
from pathlib import Path

API = "http://127.0.0.1:8188"
OUTDIR = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")
DEST = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex")

def submit(img, prefix):
    wf = {
      "1": {"class_type":"LoadImage","inputs":{"image": img}},
      "2": {"class_type":"UpscaleModelLoader","inputs":{"model_name":"RealESRGAN_x4plus.pth"}},
      "3": {"class_type":"ImageUpscaleWithModel","inputs":{"upscale_model":["2",0],"image":["1",0]}},
      "4": {"class_type":"SaveImage","inputs":{"filename_prefix":prefix,"images":["3",0]}},
    }
    req = urllib.request.Request(API+"/prompt", data=json.dumps({"prompt":wf}).encode(),
                                 headers={"Content-Type":"application/json"})
    r = json.loads(urllib.request.urlopen(req).read())
    return r["prompt_id"]

def wait_done(pid, timeout=180):
    t0=time.time()
    while time.time()-t0 < timeout:
        h = json.loads(urllib.request.urlopen(API+"/history/"+pid).read())
        if pid in h and h[pid].get("status",{}).get("completed"):
            outs = h[pid]["outputs"]
            files=[]
            for n in outs.values():
                for im in n.get("images",[]):
                    files.append(im["filename"])
            return files
        time.sleep(2)
    return None

for img, prefix in [("FVIEW_HAND_Foxhowl_Renewal_BL.png","up_hand"),
                    ("FVIEW_ARM_Foxhowl_Renewal_BL.png","up_arm")]:
    pid = submit(img, prefix)
    print("submitted", img, pid)
    files = wait_done(pid)
    print("done files:", files)
    for f in files or []:
        src = OUTDIR/f
        if src.exists():
            dst = DEST/("4x_"+f)
            shutil.copy(src, dst)
            print("copied ->", dst)
