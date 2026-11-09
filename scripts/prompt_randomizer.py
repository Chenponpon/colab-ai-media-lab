import os
import json
import random

# ==================== 1. 絕對鎖定的核心人設 (100% 符合平台規範之時尚寫真設定) ====================
CORE_PERSONA = (
    "RAW candid editorial fashion portrait photograph on 35mm Kodak Portra 400 film of three real 20-year-old French-Vietnamese mixed-race Eurasian women, "
    "not mannequins, unedited snapshot feel. "
    "All three have extremely fair, clear, translucent porcelain skin with a natural healthy flush, soft rosy undertone, "
    "visible fine pores, and subtle realistic skin texture. "
    "Slim lean hourglass figures, 165cm 50kg proportions, natural full feminine curves, slim waists."
)

# ==================== 2. 帶中文標籤的隨機多樣化維度池 (100% 合規不露點時尚寫真) ====================
FACE_SHAPES = [
    {"zh": "精緻鵝蛋臉", "en": "delicate oval face with soft feminine features"},
    {"zh": "小巧心形臉", "en": "petite heart-shaped face with expressive eyes"},
    {"zh": "立體柔和 V 臉", "en": "soft V-line face with high cheekbones"},
    {"zh": "清純圓潤娃娃臉", "en": "youthful round baby-face with innocent charm"},
    {"zh": "法亞立體下顎輪廓", "en": "sculpted delicate jawline with classic French-Asian features"},
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
        "zh": "法式精緻花卉蕾絲連身衣 (Chantilly Lace Bodysuit)",
        "category": "fashion_bodysuit",
        "needs_color": True,
        "en": "elegant French floral Chantilly lace bodysuit with lined cups"
    },
    {
        "zh": "細肩帶絲綢拼接蕾絲居家兩件組 (Silk & Lace Loungewear Set)",
        "category": "silk_loungewear",
        "needs_color": True,
        "en": "delicate silk satin and floral lace bralette and high-waisted loungewear set"
    },
    {
        "zh": "薄紗網布刺繡馬甲連身衣 (Embroidered Tulle Corset Bodysuit)",
        "category": "corset_bodysuit",
        "needs_color": True,
        "en": "fitted embroidered tulle mesh and satin corset-style bodysuit"
    },
    {
        "zh": "法式柔滑真絲細肩帶睡裙 (Silk Chiffon Camisole Slip)",
        "category": "silk_slip",
        "needs_color": True,
        "en": "luxurious draped silk chiffon camisole slip with delicate lace trim"
    },
    {
        "zh": "復古方領蕾絲滾邊緊身連體衣 (Vintage Lace-Trimmed Bustier)",
        "category": "vintage_bustier",
        "needs_color": True,
        "en": "vintage-inspired floral lace-trimmed bustier top and matching high-waist briefs"
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
        "zh": "全身站立親密互動（輕觸手臂與肩膀、微傾靠近彼此微笑）",
        "en": "standing close together facing the camera, light affectionate touches on arms and shoulders, leaning slightly toward one another with shared soft smiles, full body visible"
    },
    {
        "zh": "跪坐緊靠互動（一人下巴輕靠對方肩頭、自然放鬆直視鏡頭）",
        "en": "kneeling and sitting closely together, one resting her chin gently on another's shoulder, relaxed candid posture and warm eye contact with the camera"
    },
    {
        "zh": "並肩自然擁抱（微側身姿、柔和眼神看鏡頭、全身入鏡）",
        "en": "standing side by side in a natural candid group embrace, slight hip tilt, looking toward the lens with soft natural expressions, full body visible from head to toe"
    },
    {
        "zh": "優雅斜倚牽手（親密倚靠、展現自然曲線與柔和微笑）",
        "en": "lounging gracefully close together, playfully holding hands and leaning in with gentle candid smiles"
    },
    {
        "zh": "四分之三側身回眸（貼近彼此、微轉頭看向鏡頭展現迷人神情）",
        "en": "standing at slight three-quarter angles close to each other, turning their heads toward the camera with soft expressions, full body visible"
    }
]

BACKGROUNDS_AND_LIGHTING = [
    {
        "zh": "日式傳統和室榻榻米 ＋ 背後大型全身鏡反射背影 ＋ 障子紙窗柔和自然光",
        "en": "on Japanese tatami mats in a traditional washitsu room with a large clear mirror behind them reflecting their backs, soft natural daylight filtering through shoji paper screens"
    },
    {
        "zh": "巴黎極簡純白床單臥室 ＋ 側邊柔和晨光與自然光影（對齊參考圖風格）",
        "en": "on crisp white linen bedsheets in a minimalist sunlit Parisian bedroom against a warm off-white wall, soft diffused morning window light casting gentle shadows"
    },
    {
        "zh": "北歐落地窗陽光閣樓 ＋ 無框大型全身鏡 ＋ 黃金時刻暖陽",
        "en": "in a bright Scandinavian loft studio with floor-to-ceiling windows and a large full-length frameless mirror, bathed in soft golden-hour sunlight"
    },
    {
        "zh": "現代奢華極簡套房 ＋ 暖色洞石牆與微風吹拂的白紗簾自然光",
        "en": "in a luxury modern minimalist suite with warm travertine stone walls, sheer white curtains blowing gently, and bright natural daylight"
    },
    {
        "zh": "陽光玻璃花房 ＋ 奶油白絲絨躺椅與柔和逆光",
        "en": "on a plush cream velvet daybed in a sunlit conservatory room with soft natural backlight and airy ambient illumination"
    }
]


def generate_diversified_prompt(seed=None, **kwargs):
    """產生 100% 符合平台安全規範之「保留核心人設 + 隨機多樣化維度」Prompt 與中英雙語參數對照表 (Recipe)。"""
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

    women_descriptions = []
    women_metadata = []
    positions_en = ["The first woman on the left", "The second woman in the center", "The third woman on the right"]
    positions_zh = ["左邊女孩", "中間女孩", "右邊女孩"]

    for idx in range(3):
        att = attires[idx]
        attire_en = f"wearing a {lingerie_colors[idx]['en']} {att['en']}"
        attire_zh = f"{lingerie_colors[idx]['zh']} — {att['zh']}"

        desc = (
            f"{positions_en[idx]} has a {faces[idx]['en']}, {colors[idx]['en']} {hairs[idx]['en']}, "
            f"and {makeups[idx]['en']}, {attire_en}."
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

    full_prompt = (
        f"{CORE_PERSONA} "
        f"Each woman has distinctly different facial features, hairstyle, and styling: "
        f"{' '.join(women_descriptions)} "
        f"All three are {pose['en']}, {bg['en']}. "
        f"Photorealistic, 85mm f/1.8 lens, ultra-detailed realistic skin pores and delicate lace texture."
    )

    summary_lines = [
        f"🔑 隨機種子 (Seed): {image_seed}",
        f"🏞️ 場景與光線: {bg['zh']}",
        f"💃 姿勢與互動: {pose['zh']}",
    ]
    for w in women_metadata:
        summary_lines.append(
            f"👩 {w['position_zh']}: {w['face_zh']} | {w['hair_color_zh']}{w['hair_style_zh']} | {w['makeup_zh']} | {w['attire_zh']}"
        )

    metadata = {
        "seed": image_seed,
        "core_persona_zh": "20歲法越混血女性 × 3、極致白皙透亮瓷肌（粉嫩血色/真實毛孔）、165cm 50kg 沙漏體態",
        "background_zh": bg["zh"],
        "pose_zh": pose["zh"],
        "women": women_metadata,
        "summary_text": "\n".join(summary_lines),
        "full_prompt": full_prompt
    }
    return full_prompt, metadata


def build_gallery_html(output_dir):
    """自動掃描 outputs/ 資料夾內的所有圖片、影片、壓測報告與 *_recipe.json，生成一目了然的中文參數對照網頁 gallery_index.html"""
    recipes = sorted([f for f in os.listdir(output_dir) if f.endswith("_recipe.json")])
    videos = sorted([f for f in os.listdir(output_dir) if f.endswith(".mp4")])
    bench_path = os.path.join(output_dir, "benchmark_report.json")
    bench_html = ""
    if os.path.exists(bench_path):
        with open(bench_path, "r", encoding="utf-8") as bf:
            bdata = json.load(bf)
        bench_html = f"""
        <div class="bench-box">
            <h2>⚡ 雲端 GPU 硬體算圖與算影片極限壓測報告</h2>
            <p><strong>🖥️ 配發 GPU 型號：</strong><code>{bdata.get('gpu_name')}</code> (單卡顯存: <code>{bdata.get('vram_gb')} GB</code> | 系統 RAM: <code>{bdata.get('ram_gb')} GB</code>)</p>
            <p><strong>🖼️ 生圖平均速度與顯存峰值：</strong>每張耗時 <code>{bdata.get('avg_image_time_sec')} 秒</code> | 峰值 VRAM: <code>{bdata.get('image_peak_vram_gb')} GB</code> | 極限解析度測試: <code>{bdata.get('max_resolution_tested')}</code></p>
            <p><strong>🎬 生影片速度與顯存峰值：</strong>每支耗時 <code>{bdata.get('avg_video_time_sec')} 秒</code> | 峰值 VRAM: <code>{bdata.get('video_peak_vram_gb')} GB</code> | 影片引擎: <code>{bdata.get('video_model')}</code></p>
        </div>"""

    cards_html = []
    for r_file in recipes:
        r_path = os.path.join(output_dir, r_file)
        with open(r_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        img_file = r_file.replace("_recipe.json", ".jpg")
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

        perf_line = ""
        if meta.get("elapsed_sec"):
            perf_line = f"<p><strong>⏱️ 本張算圖耗時：</strong><code>{meta.get('elapsed_sec')} 秒</code> | <strong>📊 顯存峰值：</strong><code>{meta.get('peak_vram_gb')} GB</code> | <strong>📐 解析度：</strong><code>{meta.get('resolution')}</code></p>"

        cards_html.append(f"""
        <div class="card">
            <div class="media-col">
                <a href="{img_file}" target="_blank"><img src="{img_file}" alt="{img_file}"></a>
                <div class="fname">{img_file} (Seed: <code>{meta.get('seed')}</code>)</div>
            </div>
            <div class="info-col">
                <h3>📸 {img_file} — 生成參數配方與極限數據明細</h3>
                {perf_line}
                <p><strong>🔒 固定核心人設：</strong>{meta.get('core_persona_zh')}</p>
                <p><strong>🏞️ 抽中場景與光線：</strong>{meta.get('background_zh')}</p>
                <p><strong>💃 抽中姿勢與互動：</strong>{meta.get('pose_zh')}</p>
                <table>
                    <thead>
                        <tr><th>位置</th><th>臉型</th><th>髮色 / 髮型</th><th>妝容</th><th>時尚蕾絲穿搭款式 / 顏色</th></tr>
                    </thead>
                    <tbody>{women_rows}</tbody>
                </table>
                <details>
                    <summary>查看完整英文 Prompt (點擊展開)</summary>
                    <pre>{meta.get('full_prompt')}</pre>
                </details>
            </div>
        </div>""")

    video_cards = ""
    for v_file in videos:
        video_cards += f"""
        <div class="vid-box">
            <video controls autoplay loop muted width="320"><source src="{v_file}" type="video/mp4"></video>
            <div class="fname">🎬 {v_file}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>AI 寫實人像與動態影片 — 極限壓測與參數配方圖鑑</title>
<style>
body {{ font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; background: #121316; color: #e8eaed; margin: 0; padding: 24px; }}
h1, h2 {{ color: #f8f9fa; border-bottom: 1px solid #2d3139; padding-bottom: 10px; }}
.bench-box {{ background: #1a2332; border: 1px solid #3b5998; border-radius: 12px; padding: 18px 24px; margin-bottom: 28px; }}
.card {{ display: flex; gap: 24px; background: #1e2025; border: 1px solid #2d3139; border-radius: 12px; padding: 20px; margin-bottom: 24px; align-items: flex-start; }}
.media-col img {{ width: 300px; border-radius: 8px; object-fit: cover; border: 1px solid #3c4043; }}
.fname {{ text-align: center; margin-top: 8px; font-size: 13px; color: #9aa0a6; }}
.info-col {{ flex: 1; }}
table {{ width: 100%; border-collapse: collapse; margin: 14px 0; background: #16181c; border-radius: 8px; overflow: hidden; }}
th, td {{ padding: 10px 12px; border-bottom: 1px solid #2d3139; text-align: left; font-size: 14px; }}
th {{ background: #252830; color: #8ab4f8; }}
.badge {{ background: #28353b; color: #81d4fa; padding: 3px 8px; border-radius: 4px; font-size: 13px; }}
pre {{ background: #101214; padding: 12px; border-radius: 6px; white-space: pre-wrap; font-size: 12px; color: #bdc1c6; }}
.vid-grid {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 30px; }}
.vid-box {{ background: #1e2025; padding: 12px; border-radius: 10px; border: 1px solid #2d3139; }}
</style>
</head>
<body>
<h1>🎨 AI 寫實人像與動態影片 — 硬體極限壓測 & 隨機參數對照總覽</h1>
{bench_html}
<h2>🎬 動態影片成果 ({len(videos)} 支)</h2>
<div class="vid-grid">{video_cards if video_cards else '<p>尚無影片</p>'}</div>
<h2>📸 寫實人像照片與隨機參數配方卡 ({len(recipes)} 張)</h2>
{''.join(cards_html)}
</body>
</html>"""

    index_path = os.path.join(output_dir, "gallery_index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    return index_path
