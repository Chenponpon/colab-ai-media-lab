import os
import json
import random

# ==================== 1. 絕對鎖定的核心人設 (Core Fixed Persona) ====================
CORE_PERSONA = (
    "RAW candid documentary-style photograph on 35mm film of three real 20-year-old French-Vietnamese mixed-race Eurasian women, "
    "not models or mannequins, unedited snapshot feel. "
    "All three have extremely fair, clear, translucent porcelain skin with a natural healthy flush, soft rosy undertone, "
    "visible fine pores, and subtle realistic skin texture. "
    "Slim lean real hourglass bodies, 165cm 50kg proportions, large but natural realistic soft F-cup breasts "
    "with natural gravity, shape, and realistic skin/breast texture (not fake or enhanced), slim waists, realistic soft curves."
)

# ==================== 2. 帶中文標籤的隨機多樣化維度池 (Bilingual Randomized Pools) ====================
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
    {"zh": "沐浴後自然紅潤透亮肌", "en": "fresh post-bath natural rosy flush with clear hydrated skin"}
]

# 包含 5 種薄紗內衣 + 3 種藝術裸露 (Artistic Nudity) 層級
ATTIRE_STYLES = [
    {
        "zh": "【薄紗內衣】極薄近乎隱形透明網紗內衣組",
        "category": "sheer_lingerie",
        "needs_color": True,
        "en": "ultra-sheer almost invisible tulle mesh lingerie set with minimal delicate lace"
    },
    {
        "zh": "【薄紗內衣】法式透明蕾絲連身衣 (Bodysuit)",
        "category": "sheer_lingerie",
        "needs_color": True,
        "en": "translucent French floral Chantilly lace bodysuit"
    },
    {
        "zh": "【薄紗內衣】極薄透膚網紗內衣配高腰細帶",
        "category": "sheer_lingerie",
        "needs_color": True,
        "en": "extremely thin sheer mesh bralette and high-cut delicate briefs"
    },
    {
        "zh": "【薄紗內衣】蟬翼透明絲網吊帶睡裙",
        "category": "sheer_lingerie",
        "needs_color": True,
        "en": "gossamer-thin translucent silk-mesh camisole slip set"
    },
    {
        "zh": "【藝術裸露 Lv.1：極致透視薄紗】全透明蟬翼薄紗披肩（完全透出胸型與肌膚曲線）",
        "category": "artistic_nude_lv1_sheer_drape",
        "needs_color": True,
        "en": "unbuttoned open-front ultra-thin completely see-through gossamer silk veil draped loosely over her shoulders, leaving her bare natural breasts and hourglass torso transparently visible"
    },
    {
        "zh": "【藝術裸露 Lv.2：半裸上空 Topless】上半身赤裸上空寫真（僅穿蕾絲細帶小褲）",
        "category": "artistic_nude_lv2_topless",
        "needs_color": True,
        "en": "artistic topless glamour style with completely bare unclothed upper body showcasing natural soft full breasts, paired only with a minimal sheer lace string bikini bottom"
    },
    {
        "zh": "【藝術裸露 Lv.3：全裸人體寫真 Fine Art Nude】全身赤裸自然光藝術寫真（展現完整白皙曲線）",
        "category": "artistic_nude_lv3_full_nude",
        "needs_color": False,
        "en": "tasteful fine-art full nude style, completely unclothed bare porcelain skin glowing in soft natural light, showcasing her natural soft full breasts and slim hourglass curves"
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
        "zh": "並肩自然擁抱（微側腰臀曲線、柔和眼神看鏡頭、全身入鏡）",
        "en": "standing side by side in a natural candid group embrace, slight hip tilt, looking toward the lens with soft natural expressions, full body visible from head to toe"
    },
    {
        "zh": "優雅斜倚牽手（親密倚靠、展現自然胸腰曲線與柔和微笑）",
        "en": "lounging gracefully close together, playfully holding hands and leaning in with gentle candid smiles, showing natural body curves"
    },
    {
        "zh": "四分之三側身回眸（貼近彼此、微轉頭看向鏡頭展現迷人神情）",
        "en": "standing at slight three-quarter angles close to each other, turning their heads toward the camera with soft alluring expressions, full body visible"
    }
]

BACKGROUNDS_AND_LIGHTING = [
    {
        "zh": "日式傳統和室榻榻米 ＋ 背後大型全身鏡反射美背 ＋ 障子紙窗柔和自然光",
        "en": "on Japanese tatami mats in a traditional washitsu room with a large clear mirror behind them reflecting their full backs and bodies, soft natural daylight filtering through shoji paper screens"
    },
    {
        "zh": "巴黎極簡純白床單臥室 ＋ 側邊柔和晨光與自然光影",
        "en": "on crisp white linen bedsheets in a minimalist sunlit Parisian bedroom, soft diffused morning window light casting gentle shadows"
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


def generate_diversified_prompt(seed=None, force_artistic_nude_mode=None):
    """
    產生「保留核心人設 + 隨機多樣化維度」的 Prompt 與完整中英雙語參數對照表 (Recipe)。
    force_artistic_nude_mode:
      - None: 完全隨機（從薄紗內衣與 3 種藝術裸露中自由抽樣）
      - "all_artistic_nude": 強制三位女孩分別抽中 Lv.1 極致透視、Lv.2 半裸上空、Lv.3 全裸寫真！
    """
    rng = random.Random(seed)
    image_seed = seed if seed is not None else rng.randint(10000000, 99999999)

    faces = rng.sample(FACE_SHAPES, 3)
    hairs = rng.sample(HAIR_STYLES, 3)
    colors = rng.sample(HAIR_COLORS, 3)
    makeups = rng.sample(MAKEUP_STYLES, 3)
    lingerie_colors = rng.sample(LINGERIE_COLORS, 3)

    if force_artistic_nude_mode == "all_artistic_nude":
        nude_pool = [a for a in ATTIRE_STYLES if a["category"].startswith("artistic_nude")]
        attires = rng.sample(nude_pool, 3)
    else:
        attires = rng.sample(ATTIRE_STYLES, 3)

    pose = rng.choice(POSES_AND_INTERACTIONS)
    bg = rng.choice(BACKGROUNDS_AND_LIGHTING)

    women_descriptions = []
    women_metadata = []
    positions_en = ["The first woman on the left", "The second woman in the center", "The third woman on the right"]
    positions_zh = ["左邊女孩", "中間女孩", "右邊女孩"]

    for idx in range(3):
        att = attires[idx]
        if att["needs_color"]:
            attire_en = f"wearing a {lingerie_colors[idx]['en']} {att['en']}"
            attire_zh = f"{lingerie_colors[idx]['zh']} — {att['zh']}"
        else:
            attire_en = f"in {att['en']}"
            attire_zh = f"無衣物 — {att['zh']}"

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
        f"Photorealistic, 85mm f/1.8 lens, ultra-detailed realistic skin pores and fabric translucency."
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
        "core_persona_zh": "20歲法越混血女性 × 3、極致白皙透亮瓷肌（粉嫩血色/真實毛孔）、165cm 50kg 真實自然 F 罩杯沙漏體態",
        "background_zh": bg["zh"],
        "pose_zh": pose["zh"],
        "women": women_metadata,
        "summary_text": "\n".join(summary_lines),
        "full_prompt": full_prompt
    }
    return full_prompt, metadata


def build_gallery_html(output_dir):
    """自動掃描 outputs/ 資料夾內的所有圖片、影片與 *_recipe.json，生成一目了然的中文參數對照網頁 gallery_index.html"""
    recipes = sorted([f for f in os.listdir(output_dir) if f.endswith("_recipe.json")])
    videos = sorted([f for f in os.listdir(output_dir) if f.endswith(".mp4")])

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

        cards_html.append(f"""
        <div class="card">
            <div class="media-col">
                <a href="{img_file}" target="_blank"><img src="{img_file}" alt="{img_file}"></a>
                <div class="fname">{img_file} (Seed: <code>{meta.get('seed')}</code>)</div>
            </div>
            <div class="info-col">
                <h3>📸 {img_file} — 生成參數配方明細</h3>
                <p><strong>🔒 固定核心人設：</strong>{meta.get('core_persona_zh')}</p>
                <p><strong>🏞️ 抽中場景與光線：</strong>{meta.get('background_zh')}</p>
                <p><strong>💃 抽中姿勢與互動：</strong>{meta.get('pose_zh')}</p>
                <table>
                    <thead>
                        <tr><th>位置</th><th>臉型</th><th>髮色 / 髮型</th><th>妝容</th><th>服裝 / 藝術裸露尺度</th></tr>
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
<title>AI 寫實人像與動態影片 — 參數配方圖鑑</title>
<style>
body {{ font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; background: #121316; color: #e8eaed; margin: 0; padding: 24px; }}
h1, h2 {{ color: #f8f9fa; border-bottom: 1px solid #2d3139; padding-bottom: 10px; }}
.card {{ display: flex; gap: 24px; background: #1e2025; border: 1px solid #2d3139; border-radius: 12px; padding: 20px; margin-bottom: 24px; align-items: flex-start; }}
.media-col img {{ width: 300px; border-radius: 8px; object-fit: cover; border: 1px solid #3c4043; }}
.fname {{ text-align: center; margin-top: 8px; font-size: 13px; color: #9aa0a6; }}
.info-col {{ flex: 1; }}
table {{ width: 100%; border-collapse: collapse; margin: 14px 0; background: #16181c; border-radius: 8px; overflow: hidden; }}
th, td {{ padding: 10px 12px; border-bottom: 1px solid #2d3139; text-align: left; font-size: 14px; }}
th {{ background: #252830; color: #8ab4f8; }}
.badge {{ background: #3b2838; color: #f48fb1; padding: 3px 8px; border-radius: 4px; font-size: 13px; }}
pre {{ background: #101214; padding: 12px; border-radius: 6px; white-space: pre-wrap; font-size: 12px; color: #bdc1c6; }}
.vid-grid {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 30px; }}
.vid-box {{ background: #1e2025; padding: 12px; border-radius: 10px; border: 1px solid #2d3139; }}
</style>
</head>
<body>
<h1>🎨 AI 寫實人像與藝術裸露 — 產圖 & 產影片參數對照總覽</h1>
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


if __name__ == "__main__":
    p, meta = generate_diversified_prompt(force_artistic_nude_mode="all_artistic_nude")
    print(meta["summary_text"])
