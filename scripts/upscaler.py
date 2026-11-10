import os
import sys
import torch
from PIL import Image
import torchvision.transforms.functional as TF

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "RealESRGAN_x4plus.pth")

_cached_model = None

def get_upscaler_model(model_path=DEFAULT_MODEL_PATH):
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    
    if not os.path.exists(model_path):
        import urllib.request
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
        print(f"📥 正在下載 RealESRGAN_x4plus.pth 模型至 {model_path}...")
        urllib.request.urlretrieve(url, model_path)
    
    from spandrel import ModelLoader
    device = "cuda" if torch.cuda.is_available() else "cpu"
    loaded = ModelLoader().load_from_file(model_path).to(device)
    loaded.eval()
    _cached_model = (loaded, device)
    return _cached_model

def upscale_image_realesrgan(image: Image.Image, target_size=None) -> Image.Image:
    """
    使用 Real-ESRGAN 進行 4x AI 神經網路超解析度修復放大，
    自動補足微觀皮膚毛孔、瞳孔高光、睫毛與蕾絲紋理細節。
    """
    model, device = get_upscaler_model()
    
    img_tensor = TF.to_tensor(image.convert("RGB")).unsqueeze(0).to(device)
    
    with torch.no_grad():
        out_tensor = model(img_tensor)
        out_tensor = out_tensor.squeeze(0).cpu().clamp(0, 1)
        
    out_img = TF.to_pil_image(out_tensor)
    
    if target_size is not None:
        out_img = out_img.resize(target_size, Image.LANCZOS)
        
    return out_img

if __name__ == "__main__":
    print("✅ Real-ESRGAN 模組已就位！")
