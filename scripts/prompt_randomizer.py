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

# ==================== 2. 隨機多樣化維度池 (Randomized Pools) ====================
FACE_SHAPES = [
    "delicate oval face with soft feminine features",
    "petite heart-shaped face with expressive eyes",
    "soft V-line face with high cheekbones",
    "youthful round baby-face with innocent charm",
    "sculpted delicate jawline with classic French-Asian features",
    "graceful diamond-shaped face with deep-set eyes"
]

HAIR_STYLES = [
    "long flowing wavy hair",
    "silky straight waist-length hair",
    "chic chin-length French bob haircut",
    "effortless messy high bun with loose face-framing tendrils",
    "shoulder-length layered collarbone cut",
    "long romantic half-up waves",
    "sleek low ponytail withwispy bangs"
]

HAIR_COLORS = [
    "jet black",
    "deep espresso brown",
    "warm chestnut brown",
    "dark chocolate brown",
    "caramel ash brown",
    "rich honey auburn",
    "soft black-brown"
]

MAKEUP_STYLES = [
    "dewy bare-faced no-makeup look with glossy lips",
    "soft French rose tint on lips and cheeks with subtle freckles",
    "luminous glass-skin finish with peach-pink blush",
    "delicate natural winged eyeliner and soft coral-pink lips",
    "fresh post-bath natural rosy flush with clear hydrated skin"
]

LINGERIE_STYLES = [
    "ultra-sheer almost invisible tulle mesh lingerie set with minimal delicate lace",
    "translucent French floral Chantilly lace bodysuit",
    "extremely thin sheer mesh bralette and high-cut delicate briefs",
    "gossamer-thin translucent silk-mesh camisole slip set",
    "delicate sheer embroidered tulle corset-style bodysuit"
]

LINGERIE_COLORS = [
    "pure pearl white",
    "midnight black",
    "deep burgundy wine red",
    "champagne blush nude",
    "muted dusty rose pink",
    "soft lavender mist",
    "pale ice blue",
    "champagne ivory"
]

POSES_AND_INTERACTIONS = [
    "standing close together facing the camera, light affectionate touches on arms and shoulders, leaning slightly toward one another with shared soft smiles, full body visible",
    "kneeling and sitting closely together, one resting her chin gently on another's shoulder, relaxed candid posture and warm eye contact with the camera",
    "standing side by side in a natural candid group embrace, slight hip tilt, looking toward the lens with soft natural expressions, full body visible from head to toe",
    "lounging gracefully close together, playfully holding hands and leaning in with gentle candid smiles, showing natural body curves",
    "standing at slight three-quarter angles close to each other, turning their heads toward the camera with soft alluring expressions, full body visible"
]

BACKGROUNDS_AND_LIGHTING = [
    "on Japanese tatami mats in a traditional washitsu room with a large clear mirror behind them reflecting their full backs and bodies, soft natural daylight filtering through shoji paper screens",
    "on crisp white linen bedsheets in a minimalist sunlit Parisian bedroom, soft diffused morning window light casting gentle shadows",
    "in a bright Scandinavian loft studio with floor-to-ceiling windows and a large full-length frameless mirror, bathed in soft golden-hour sunlight",
    "in a luxury modern minimalist suite with warm travertine stone walls, sheer white curtains blowing gently, and bright natural daylight",
    "on a plush cream velvet daybed in a sunlit conservatory room with soft natural backlight and airy ambient illumination"
]


def generate_diversified_prompt(seed=None):
    """每次呼叫都會保留「法越混血、白皙透亮膚質、165cm/50kg/自然F罩杯沙漏身材」核心人設，
    並自動為三位女孩隨機抽樣不重複的臉型、髮型、髮色、妝容、服裝款式/顏色、姿勢與場景！"""
    rng = random.Random(seed)

    faces = rng.sample(FACE_SHAPES, 3)
    hairs = rng.sample(HAIR_STYLES, 3)
    colors = rng.sample(HAIR_COLORS, 3)
    makeups = rng.sample(MAKEUP_STYLES, 3)
    lingerie_styles = rng.sample(LINGERIE_STYLES, 3)
    lingerie_colors = rng.sample(LINGERIE_COLORS, 3)

    pose = rng.choice(POSES_AND_INTERACTIONS)
    bg = rng.choice(BACKGROUNDS_AND_LIGHTING)

    women_descriptions = []
    positions = ["The first woman on the left", "The second woman in the center", "The third woman on the right"]
    for idx in range(3):
        desc = (
            f"{positions[idx]} has a {faces[idx]}, {colors[idx]} {hairs[idx]}, "
            f"and {makeups[idx]}, wearing a {lingerie_colors[idx]} {lingerie_styles[idx]}."
        )
        women_descriptions.append(desc)

    full_prompt = (
        f"{CORE_PERSONA} "
        f"Each woman has distinctly different facial features, hairstyle, and styling: "
        f"{' '.join(women_descriptions)} "
        f"All three are {pose}, {bg}. "
        f"Photorealistic, 85mm f/1.8 lens, ultra-detailed realistic skin pores and fabric translucency."
    )

    metadata = {
        "women": [
            {
                "position": positions[i],
                "face_shape": faces[i],
                "hair_color": colors[i],
                "hair_style": hairs[i],
                "makeup": makeups[i],
                "lingerie_color": lingerie_colors[i],
                "lingerie_style": lingerie_styles[i]
            }
            for i in range(3)
        ],
        "pose": pose,
        "background": bg,
        "full_prompt": full_prompt
    }
    return full_prompt, metadata


if __name__ == "__main__":
    for i in range(2):
        p, meta = generate_diversified_prompt()
        print(f"=== 隨機組合範例 #{i+1} ===")
        print(p)
        print()
