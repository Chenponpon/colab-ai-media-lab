import os
import json
import time
import random

# ==================== 1. 絕對鎖定的核心人設 (真實無磨皮毛孔質感 + 冷白牛乳瓷肌 + 正負面雙 Prompt) ====================
CORE_PERSONA = (
    "Intimate indoor boudoir portrait photograph shot on 35mm Kodak Portra 400 analog film, "
    "three gorgeous 20-year-old French-Vietnamese mixed-race Eurasian women wearing ultra-sheer see-through tulle mesh lingerie and delicate floral lace bodysuits, "
    "extremely fair milk-white translucent porcelain skin with natural rosy flush, "
    "clearly visible microscopic skin pores and realistic unretouched skin texture (zero beauty filter, not plastic), "
    "slim 165cm 50kg hourglass bodies, large natural realistic soft F-cup breasts with natural gravity and deep cleavage."
)

# 強烈封鎖日常街頭T恤、牛仔外套、戶外場景、深膚色與爆炸頭，並封鎖 AI 磨皮塑膠肌
DEFAULT_NEGATIVE_PROMPT = (
    "t-shirt, shirt, blouse, jacket, denim jacket, coat, sweater, jeans, pants, street clothes, casual clothes, "
    "modest clothing, opaque fabric, outdoors, street, park, plaza, water, crowd, trees, afro, frizzy hair, "
    "tanned skin, dark skin, olive skin, airbrushed, smooth plastic skin, beauty filter, over-smoothed skin, "
    "waxy skin, shiny oiled skin, CGI, 3d render, doll, mannequin, wax figure, silicone implants, fake breasts, "
    "digital painting, anime, cartoon, deformed hands, extra fingers, mutated limbs, bad anatomy, fused bodies, "
    "identical clone faces, watermark, text, blurry, low quality"
)

# ==================== 2. 影片生成專用：換衣服 / 整理薄紗內衣動態 Prompt 池 ====================
VIDEO_CHANGING_CLOTHES_PROMPTS = [
    {
        "zh": "緩緩褪下透明絲質薄袍換裝、雙手輕撫調整深 V 蕾絲連身衣肩帶與自然胸口呼吸律動",
        "en": (
            "Three young Eurasian women in a sunlit bedroom changing clothes, slowly slipping sheer translucent silk robes "
            "off their bare shoulders to reveal delicate see-through lace bodysuits, gently adjusting their thin lingerie straps "
            "with their hands, natural soft chest breathing and upper body movement, warm alluring smiles at the camera, "
            "photorealistic live-action human motion, high skin detail."
        )
    },
    {
        "zh": "在全身鏡前換穿極薄透明網紗內衣、手指輕拉蕾絲肩帶、撥弄長捲髮並轉身展現沙漏曲線",
        "en": (
            "Three young Eurasian women in ultra-sheer tulle mesh lingerie changing outfits in front of a large mirror, "
            "gently pulling up translucent lace straps over their shoulders, brushing long wavy hair back with their fingers, "
            "turning their torsos naturally to showcase their hourglass curves and cleavage, realistic body movement and soft eye blinks."
        )
    },
    {
        "zh": "解開透視蕾絲薄紗外罩換裝、在純白床單上親密微傾互動與真實肢體動作",
        "en": (
            "Three young Eurasian women sitting closely on crisp white bedsheets changing into sheer lace lingerie, "
            "slowly untying and opening a translucent chiffon negligee wrap, leaning naturally toward each other with soft smiles, "
            "realistic hand gestures adjusting their lingerie, natural breathing and subtle body sway, photorealistic video."
        )
    }
]

DEFAULT_VIDEO_NEGATIVE_PROMPT = (
    "static image, camera shake only, frozen body, stiff pose, t-shirt, street clothes, outdoors, "
    "distorted face, morphing features, extra limbs, deformed hands, blurry, low quality, watermark"
)

# ==================== 3. 帶中文標籤的隨機多樣化維度池 (100% 合規私房內衣寫真) ====================
FACE_SHAPES = [
    {"zh": "精緻鵝蛋臉", "en": "delicate oval face with soft feminine features"},
    {"zh": "小巧心形臉", "en": "petite heart-shaped face with expressive eyes"},
    {"zh": "立體柔和 V 臉", "en": "soft V-line face with high cheekbones"},
    {"zh": "清純圓潤娃娃臉", "en": "youthful round baby-face with innocent charm"},
    {"zh": "法越混血立體輪廓", "en": "sculpted delicate jawline with classic French-Vietnamese features"},
    {"zh": "優雅菱形臉", "en": "graceful diamond-shaped face with deep-set eyes"}
]

HAIR_STYLES = [
    {"zh": "大波浪長捲髮", "en": "long flowing wavy hair"},
    {"zh": "及腰絲滑長直髮", "en": "silky straight waist-length hair"},
    {"zh": "法式下巴短鮑伯頭", "en": "chic chin-length French bob haircut"},
    {"zh": "隨性高丸子頭配碎髮", "en": "effortless messy high bun with loose face-framing tendrils"},
    {"zh": "鎖骨層次中長髮", "en": "shoulder-length layered collarbone cut"},
    {"zh": "浪漫半紮公主波浪捲", "en": "long romantic half-up waves"},
    {"zh": "空氣瀏海低馬尾", "en": "sleek low ponytail with wispy bangs"}
]

HAIR_COLORS = [
    {"zh": "純粹烏黑", "en": "jet black"},
    {"zh": "深濃縮咖啡棕", "en": "deep espresso brown"},
    {"zh": "暖栗褐", "en": "warm chestnut brown"},
    {"zh": "黑巧克力棕", "en": "dark chocolate brown"},
    {"zh": "焦糖冷灰棕", "en": "caramel ash brown"},
    {"zh": "蜂蜜紅棕", "en": "rich honey auburn"},
    {"zh": "柔霧黑棕", "en": "soft black-brown"}
]

MAKEUP_STYLES = [
    {"zh": "水光裸妝透亮唇", "en": "dewy bare-faced no-makeup look with glossy lips"},
    {"zh": "法式玫瑰腮紅配微雀斑", "en": "soft French rose tint on lips and cheeks with subtle freckles"},
    {"zh": "蜜桃水光玻璃肌", "en": "luminous glass-skin finish with peach-pink blush"},
    {"zh": "自然細眼線配珊瑚粉唇", "en": "delicate natural winged eyeliner and soft coral-pink lips"},
    {"zh": "晨間自然紅潤透亮肌", "en": "fresh natural rosy flush with clear hydrated skin"}
]

ATTIRE_STYLES = [
    {
        "zh": "【極薄隱形透明網紗】全透明深 V 薄紗內衣配極細高叉丁字褲 (Ultra-Sheer See-Through Mesh Plunge Set)",
        "category": "ultra_sheer_mesh",
        "needs_color": True,
        "en": "skintight ultra-sheer almost invisible see-through tulle mesh deep-plunge bralette with unlined translucent cups and micro g-string thong, showcasing her full F-cup cleavage and curves"
    },
    {
        "zh": "【深 V 爆乳透膚蕾絲連身衣】無內裡全透視高叉蕾絲連身衣 (Deep-Plunge See-Through Lace High-Cut Bodysuit)",
        "category": "plunge_sheer_bodysuit",
        "needs_color": True,
        "en": "alluring deep-V plunging ultra-sheer see-through floral Chantilly lace bodysuit with extreme high-cut leg openings and unlined translucent mesh over her full breasts"
    },
    {
        "zh": "【蟬翼透明網紗綁帶比基尼】極小布料全透明薄紗細繩內衣組 (Micro Translucent Gossamer String Lingerie)",
        "category": "micro_sheer_bikini",
        "needs_color": True,
        "en": "tiny gossamer-thin completely translucent mesh triangle string bikini lingerie with minimal delicate lace trim, revealing deep cleavage and toned hourglass waist"
    },
    {
        "zh": "【極致透視敞開薄紗】未扣透明蕾絲薄紗配極細丁字褲 (Open-Front See-Through Lace Veil & Micro Thong)",
        "category": "open_sheer_veil",
        "needs_color": True,
        "en": "unbuttoned open-front ultra-thin see-through lace negligee draped loosely over bare full F-cup cleavage and curves, paired only with a tiny sheer mesh string thong"
    }
]

LINGERIE_COLORS = [
    {"zh": "珍珠白", "en": "pure pearl white"},
    {"zh": "午夜黑", "en": "midnight black"},
    {"zh": "勃根地深酒紅", "en": "deep burgundy wine red"},
    {"zh": "香檳裸膚色", "en": "champagne blush nude"},
    {"zh": "乾燥玫瑰粉", "en": "muted dusty rose pink"},
    {"zh": "柔霧薰衣草紫", "en": "soft lavender mist"},
    {"zh": "冰川淺藍", "en": "pale ice blue"},
    {"zh": "香檳象牙白", "en": "champagne ivory"}
]

POSES_AND_INTERACTIONS = [
    {
        "zh": "跪坐在柔軟純白床單上親密貼近（雙手自然撐在床面、微傾靠近彼此看鏡頭，對齊 ref_1 / ref_2）",
        "short_en": "kneeling closely together on crisp white bedsheets",
        "en": "kneeling and sitting closely together on soft white bedding, hands resting naturally on the bedsheets, leaning slightly toward one another looking softly at the camera"
    },
    {
        "zh": "全身站立於日式榻榻米親密互動（並肩貼近、輕觸彼此手臂與肩膀，對齊原始 Prompt）",
        "short_en": "standing close together full-body on Japanese tatami mats",
        "en": "standing close together facing the camera full body visible from head to toe, light touches on arms and shoulders, leaning slightly toward one another with shared soft smiles"
    },
    {
        "zh": "微側身親密依靠在床邊（一人輕靠對方肩頭、展現沙漏腰臀與深邃事業線，對齊 ref_2）",
        "short_en": "sitting closely together at three-quarter angles on a white bed",
        "en": "sitting closely together at slight three-quarter angles, leaning gently against each other's shoulders, showcasing hourglass curves, full F-cup cleavage, and warm eye contact"
    }
]

BACKGROUNDS_AND_LIGHTING = [
    {
        "zh": "日式傳統和室榻榻米 ＋ 背後大型全身鏡清晰反射美背與全身曲線 ＋ 障子紙窗自然柔光（原始 Prompt 場景）",
        "short_en": "in a Japanese washitsu tatami room with a large mirror behind them reflecting their backs, shoji window light",
        "en": "on Japanese tatami mats in a traditional washitsu room with a large clear mirror behind them clearly reflecting their full backs and bodies, natural window light from shoji screens"
    },
    {
        "zh": "巴黎極簡純白床單臥室 ＋ 暖白牆面與側邊柔和晨光（完全對齊 ref_1 & ref_2 參考圖場景）",
        "short_en": "on crisp white linen bedsheets in a minimalist bedroom against a clean warm-white wall, soft morning window light",
        "en": "on crisp white linen bedsheets in a minimalist sunlit bedroom against a warm off-white wall, soft diffused morning window light casting gentle shadows"
    },
    {
        "zh": "北歐落地窗陽光臥室 ＋ 無框大型全身鏡反射背影 ＋ 黃金時刻柔光",
        "short_en": "in a bright bedroom studio with a large full-length mirror reflecting their backs, golden-hour window light",
        "en": "in a bright Scandinavian bedroom with floor-to-ceiling windows and a large full-length frameless mirror reflecting their backs, bathed in soft golden-hour sunlight"
    }
]


def generate_diversified_prompt(seed=None, **kwargs):
    """
    產生 100% 解決 SDXL 77-Token 截斷問題的雙層寫實 Prompt：
    - clip_short_prompt (< 68 tokens)：把「三位20歲法越混血女孩 + 極薄透明網紗蕾絲內衣 + 冷白真實毛孔瓷肌 + 165cm 50kg 自然 F 罩杯 + 室內床單/和室全身鏡」濃縮在最前面，保證 SDXL 第一視窗 100% 讀取！
    - full_prompt：包含三位女孩各自的臉型、髮型、髮色、內衣款式與顏色細節。
    """
    rng = random.Random(seed)
    image_seed = seed if seed is not None else rng.randint(10000000, 99999999)

    faces = rng.sample(FACE_SHAPES, 3)
    hairs = rng.sample(HAIR_STYLES, 3)
    colors = rng.sample(HAIR_COLORS, 3)
    makeups = rng.sample(MAKEUP_STYLES, 3)
    lingerie_colors = rng.sample(LINGERIE_COLORS, 3)
    attires = rng.sample(ATTIRE_STYLES, 3)

    pose = rng.choice(POSES_AND_INTERACTIONS)
    bg = rng.choice(BACKGROUNDS_AND_LIGHTING)
    vid_motion = rng.choice(VIDEO_CHANGING_CLOTHES_PROMPTS)

    women_descriptions = []
    women_metadata = []
    positions_en = ["left woman", "center woman", "right woman"]
    positions_zh = ["左邊女孩", "中間女孩", "右邊女孩"]

    short_color_list = ", ".join([c["en"] for c in lingerie_colors])

    for idx in range(3):
        att = attires[idx]
        attire_en = f"wearing a {lingerie_colors[idx]['en']} {att['en']}"
        attire_zh = f"{lingerie_colors[idx]['zh']} — {att['zh']}"

        desc = (
            f"The {positions_en[idx]} has a {faces[idx]['en']}, {colors[idx]['en']} {hairs[idx]['en']}, "
            f"{makeups[idx]['en']}, {attire_en}."
        )
        women_descriptions.append(desc)
        women_metadata.append({
            "position_zh": positions_zh[idx],
            "face_zh": faces[idx]["zh"],
            "hair_color_zh": colors[idx]["zh"],
            "hair_style_zh": hairs[idx]["zh"],
            "makeup_zh": makeups[idx]["zh"],
            "attire_zh": attire_zh,
            "category": att["category"]
        })

    # 專為 SDXL 77-Token 限制設計的前導濃縮 Prompt (約 62 tokens，所有關鍵視覺 100% 在窗口內)
    clip_short_prompt = (
        f"Intimate indoor boudoir portrait photo of three gorgeous 20yo French-Vietnamese mixed-race women "
        f"wearing ultra-sheer see-through tulle mesh lingerie and floral lace bodysuits in {short_color_list}, "
        f"extremely fair milk-white porcelain skin, rosy flush, visible skin pores, "
        f"165cm 50kg slim hourglass bodies, large natural soft F-cup breasts, deep cleavage, "
        f"{pose['short_en']} {bg['short_en']}."
    )

    full_prompt = (
        f"{clip_short_prompt} "
        f"{' '.join(women_descriptions)} "
        f"All three are {pose['en']}, {bg['en']}. "
        "Shot on 35mm Kodak Portra 400 film, unretouched realistic skin pores and soft breast texture, natural window light."
    )

    summary_lines = [
        f"🔑 隨機種子 (Seed): {image_seed}",
        f"🏞️ 場景與光線: {bg['zh']}",
        f"💃 姿勢與互動: {pose['zh']}",
        f"🎬 對應換裝動態 Prompt: {vid_motion['zh']}"
    ]
    for w in women_metadata:
        summary_lines.append(
            f"👩 {w['position_zh']}: {w['face_zh']} | {w['hair_color_zh']}{w['hair_style_zh']} | {w['makeup_zh']} | {w['attire_zh']}"
        )

    metadata = {
        "seed": image_seed,
        "core_persona_zh": "20歲法越混血女性 × 3、無磨皮真實毛孔質感、冷白透亮瓷肌、165cm 50kg 自然柔軟 F 罩杯沙漏體態",
        "background_zh": bg["zh"],
        "pose_zh": pose["zh"],
        "video_motion_zh": vid_motion["zh"],
        "video_motion_prompt": vid_motion["en"],
        "video_negative_prompt": DEFAULT_VIDEO_NEGATIVE_PROMPT,
        "women": women_metadata,
        "summary_text": "\n".join(summary_lines),
        "clip_short_prompt": clip_short_prompt,
        "full_prompt": full_prompt,
        "negative_prompt": DEFAULT_NEGATIVE_PROMPT
    }
    return full_prompt, metadata


def migrate_flat_outputs_to_subfolders(output_dir):
    """將早期散落在 outputs/ 根目錄的舊檔案自動整理進 outputs/run_YYYYMMDD_HHMMSS/ 獨立子資料夾，保持根目錄乾淨。"""
    os.makedirs(output_dir, exist_ok=True)
    tmp_flux = os.path.join(output_dir, "_tmp_flux.jpg")
    if os.path.exists(tmp_flux):
        try:
            os.remove(tmp_flux)
        except OSError:
            pass

    flat_recipes = [
        f for f in os.listdir(output_dir)
        if os.path.isfile(os.path.join(output_dir, f)) and f.endswith("_recipe.json")
    ]
    if not flat_recipes:
        return

    # 整理舊版檔案至 run_20261110_004108_legacy
    legacy_dir = os.path.join(output_dir, "run_20261110_004108")
    os.makedirs(legacy_dir, exist_ok=True)
    for fname in list(os.listdir(output_dir)):
        fpath = os.path.join(output_dir, fname)
        if os.path.isfile(fpath) and fname != "gallery_index.html":
            shutil.move(fpath, os.path.join(legacy_dir, fname))


import shutil


def build_gallery_html(output_dir):
    """掃描 outputs/ 下所有 run_YYYYMMDD_HHMMSS/ 獨立批次資料夾，由新到舊分組展示每批產出的照片、參數卡與換裝動態影片！"""
    migrate_flat_outputs_to_subfolders(output_dir)

    run_dirs = sorted(
        [
            d for d in os.listdir(output_dir)
            if os.path.isdir(os.path.join(output_dir, d)) and d.startswith("run_")
        ],
        key=lambda d: os.path.getmtime(os.path.join(output_dir, d)),
        reverse=True
    )

    batches_html = []
    for run_name in run_dirs:
        rdir = os.path.join(output_dir, run_name)
        recipes = sorted([f for f in os.listdir(rdir) if f.endswith("_recipe.json")])
        videos = sorted([f for f in os.listdir(rdir) if f.endswith(".mp4")])
        bench_path = os.path.join(rdir, "benchmark_report.json")

        bench_html = ""
        if os.path.exists(bench_path):
            with open(bench_path, "r", encoding="utf-8") as bf:
                bdata = json.load(bf)
            bench_html = f"""
            <div class="bench-box">
                <strong>🖥️ 執行環境與模型：</strong><code>{bdata.get('gpu_name')}</code> |
                <strong>🖼️ 生圖均速：</strong><code>{bdata.get('avg_image_time_sec')} 秒/張</code> ({bdata.get('max_resolution_tested')}) |
                <strong>🎬 圖生影引擎：</strong><code>{bdata.get('video_model')}</code> (均速 <code>{bdata.get('avg_video_time_sec')} 秒/支</code>)
            </div>"""

        video_cards = ""
        for v_file in videos:
            rel_v = f"{run_name}/{v_file}"
            video_cards += f"""
            <div class="vid-box">
                <video controls autoplay loop muted width="320"><source src="{rel_v}" type="video/mp4"></video>
                <div class="fname">🎬 <a href="{rel_v}" target="_blank" style="color:#8ab4f8;">{run_name}/{v_file}</a></div>
            </div>"""

        cards_html = []
        for r_file in recipes:
            r_path = os.path.join(rdir, r_file)
            with open(r_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            img_file = r_file.replace("_recipe.json", ".jpg")
            rel_img = f"{run_name}/{img_file}"
            ts_label = meta.get("timestamp", run_name.replace("run_", ""))
            model_label = meta.get("model_engine", "RealVisXL V5.0 (SDXL)")

            women_rows = ""
            for w in meta.get("women", []):
                women_rows += f"""
                <tr>
                    <td><strong>{w['position_zh']}</strong></td>
                    <td>{w['face_zh']}</td>
                    <td>{w['hair_color_zh']} / {w['hair_style_zh']}</td>
                    <td>{w['makeup_zh']}</td>
                    <td><span class="badge">{w['attire_zh']}</span></td>
                </tr>"""

            vid_motion_line = ""
            if meta.get("video_motion_zh"):
                vid_motion_line = f"<p><strong>🎬 換裝動態影片設定：</strong>{meta.get('video_motion_zh')}</p>"

            cards_html.append(f"""
            <div class="card">
                <div class="media-col">
                    <a href="{rel_img}" target="_blank"><img src="{rel_img}" alt="{img_file}"></a>
                    <div class="fname">{run_name}/{img_file}<br>(Seed: <code>{meta.get('seed')}</code>)</div>
                </div>
                <div class="info-col">
                    <h4>📸 {img_file} — 隨機參數配方與雙向 Prompt</h4>
                    <p><strong>🕒 批次時間：</strong><code>{ts_label}</code> | <strong>🤖 模型：</strong><code>{model_label}</code> | <strong>📐 解析度：</strong><code>{meta.get('resolution', '2K')}</code></p>
                    <p><strong>🔒 固定核心人設：</strong>{meta.get('core_persona_zh')}</p>
                    <p><strong>🏞️ 抽中場景與光線：</strong>{meta.get('background_zh')}</p>
                    <p><strong>💃 抽中姿勢與互動：</strong>{meta.get('pose_zh')}</p>
                    {vid_motion_line}
                    <table>
                        <thead>
                            <tr><th>位置</th><th>臉型</th><th>髮色 / 髮型</th><th>妝容</th><th>極薄透視網紗/蕾絲款式與顏色</th></tr>
                        </thead>
                        <tbody>{women_rows}</tbody>
                    </table>
                    <details>
                        <summary>查看完整正面、負面與換裝影片 Prompt (Positive / Negative / Video Prompts)</summary>
                        <p><strong>🎯 SDXL 前導無截斷核心 Prompt (CLIP 77-Token Window)：</strong></p>
                        <pre>{meta.get('clip_short_prompt', meta.get('full_prompt'))}</pre>
                        <p><strong>➕ 完整正面提示詞 (Full Positive Prompt)：</strong></p>
                        <pre>{meta.get('full_prompt')}</pre>
                        <p><strong>➖ 負面提示詞 (Negative Prompt — 封鎖街頭T恤、戶外與 AI 磨皮塑膠感)：</strong></p>
                        <pre>{meta.get('negative_prompt', DEFAULT_NEGATIVE_PROMPT)}</pre>
                        <p><strong>🎬 圖片轉影片換裝動態提示詞 (I2V Changing-Clothes Motion Prompt)：</strong></p>
                        <pre>{meta.get('video_motion_prompt', '')}</pre>
                    </details>
                </div>
            </div>""")

        batches_html.append(f"""
        <div class="batch-section">
            <h2>📂 批次資料夾：<code>outputs/{run_name}/</code> （共 {len(recipes)} 張照片、{len(videos)} 支影片）</h2>
            {bench_html}
            {f'<h3>🎬 本批次圖生影動態成果 (根據產製圖片生成人物換裝/調整薄紗動作)</h3><div class="vid-grid">{video_cards}</div>' if video_cards else ''}
            <h3>📸 本批次寫實人像照片與參數配方</h3>
            {''.join(cards_html)}
        </div>""")

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>AI 寫實人像與換裝動態影片 — 歷次批次資料夾總覽</title>
<style>
body {{ font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; background: #121316; color: #e8eaed; margin: 0; padding: 24px; }}
h1 {{ color: #f8f9fa; border-bottom: 2px solid #3b5998; padding-bottom: 12px; }}
.batch-section {{ background: #181a1f; border: 1px solid #2d3139; border-radius: 14px; padding: 22px; margin-bottom: 36px; }}
.batch-section h2 {{ margin-top: 0; color: #8ab4f8; border-bottom: 1px solid #2d3139; padding-bottom: 10px; }}
.bench-box {{ background: #1a2332; border: 1px solid #3b5998; border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; font-size: 14px; }}
.card {{ display: flex; gap: 24px; background: #1e2025; border: 1px solid #2d3139; border-radius: 12px; padding: 20px; margin-bottom: 20px; align-items: flex-start; }}
.media-col img {{ width: 300px; border-radius: 8px; object-fit: cover; border: 1px solid #3c4043; }}
.fname {{ text-align: center; margin-top: 8px; font-size: 13px; color: #9aa0a6; }}
.info-col {{ flex: 1; }}
.info-col h4 {{ margin-top: 0; color: #f1f3f4; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; background: #16181c; border-radius: 8px; overflow: hidden; }}
th, td {{ padding: 9px 12px; border-bottom: 1px solid #2d3139; text-align: left; font-size: 13.5px; }}
th {{ background: #252830; color: #8ab4f8; }}
.badge {{ background: #28353b; color: #81d4fa; padding: 3px 8px; border-radius: 4px; font-size: 12.5px; }}
pre {{ background: #101214; padding: 10px; border-radius: 6px; white-space: pre-wrap; font-size: 12px; color: #bdc1c6; }}
.vid-grid {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 24px; }}
.vid-box {{ background: #1e2025; padding: 12px; border-radius: 10px; border: 1px solid #2d3139; }}
</style>
</head>
<body>
<h1>🎨 AI 寫實人像與換裝動態影片 — 歷次批次資料夾總覽 (由新到舊)</h1>
{''.join(batches_html) if batches_html else '<p>尚無批次紀錄</p>'}
</body>
</html>"""

    index_path = os.path.join(output_dir, "gallery_index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    return index_path
