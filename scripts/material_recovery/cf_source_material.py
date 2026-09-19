from __future__ import annotations

import configparser
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageStat


SOURCE_PROXY_GAIN = 0.75
SOURCE_ENV_PROXY_GAIN = 1.5
SOURCE_EXPONENT_SCALE = 8.0
SOURCE_LIGHT_INFLUENCE_SCALE = 2.0
SOURCE_MIN_LIT_FRACTION = 0.2
SOURCE_MAX_LIT_FRACTION = 0.6


def parse_cfg(path: Path) -> dict:
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.optionxform = str
    parser.read_string(path.read_text(encoding="utf-8-sig", errors="replace"))
    return {section: dict(parser.items(section)) for section in parser.sections()}


def number(values: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return default


def enabled(values: dict, key: str) -> bool:
    return number(values, key) != 0.0


def classify_player_view(cfg: dict) -> dict:
    techniques = cfg.get("Techniques", {})
    properties = cfg.get("Properties", {})
    specular = enabled(techniques, "SpecularMappingEnabled")
    envcube = enabled(techniques, "EnvCubeMappingEnabled")
    normal = enabled(techniques, "NormalMappingEnabled")
    usage = int(number(properties, "EnvCubeUsage"))
    refraction = number(properties, "RefractionIndex")
    transform_y = number(properties, "CubeMapTransformY")
    transformed_snell = envcube and usage == 2 and (refraction != 0.0 or transform_y != 0.0)
    if transformed_snell:
        family = "player_view_alpha_snell_transformed_cube"
        strategy = "lit_specular_proxy"
    elif envcube:
        family = "player_view_reflective"
        strategy = "native_envmap_candidate"
    elif specular:
        family = "player_view_specular"
        strategy = "lit_specular"
    else:
        family = "player_view_diffuse"
        strategy = "diffuse"
    observed_exponent = max(0.0, number(properties, "SpecularPower") * 0.25)
    source_exponent = max(1, min(64, int(round(observed_exponent * SOURCE_EXPONENT_SCALE))))
    return {
        "family": family,
        "strategy": strategy,
        "specular_enabled": specular,
        "envcube_enabled": envcube,
        "normal_enabled": normal,
        "envcube_usage": usage,
        "refraction_index": refraction,
        "reflection_index": number(properties, "ReflectionIndex"),
        "cubemap_transform_y": transform_y,
        "light_brightness": number(properties, "LightBrightness", 1.0),
        "diffuse_boost": number(properties, "DiffuseBoost"),
        "ambient_light_color": number(properties, "AmbientLightColor"),
        "envcube_brightness": number(properties, "EnvCubeMapBrightness", 1.0),
        "specular_power_cfg": number(properties, "SpecularPower"),
        "specular_exponent_observed": observed_exponent,
        "source_phong_exponent": source_exponent,
    }


def build_lit_specular_proxy(
    diffuse: Image.Image,
    specular: Image.Image,
    alpha: Image.Image,
    profile: dict,
    size: tuple[int, int],
    cubemap: Image.Image | None = None,
) -> tuple[Image.Image, Image.Image, Image.Image, Image.Image, dict]:
    base = diffuse.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    spec = specular.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    channels = alpha.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    base_array = np.asarray(base, dtype=np.float32) / 255.0
    spec_array = np.asarray(spec, dtype=np.float32) / 255.0
    alpha_array = np.asarray(channels, dtype=np.float32) / 255.0
    weights = np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    spec_energy = spec_array * alpha_array[:, :, 1:2] if profile["specular_enabled"] else np.zeros_like(base_array)
    cube_rgb = np.array([value / 255.0 for value in ImageStat.Stat(
        cubemap.convert("RGB") if cubemap is not None else Image.new("RGB", (1, 1), "white")
    ).mean], dtype=np.float32)
    env_brightness = max(0.0, profile["envcube_brightness"])
    env_energy = (
        alpha_array[:, :, 2:3] * cube_rgb * env_brightness
        if profile["envcube_enabled"] and cubemap is not None else np.zeros_like(base_array)
    )
    filter_radius = max(1.0, size[0] / 512.0)
    env_response = np.clip(env_energy @ weights, 0.0, 1.0)
    env_response_image = Image.fromarray(np.uint8(np.round(env_response * 255.0)), "L")
    env_response_image = env_response_image.filter(ImageFilter.GaussianBlur(filter_radius))
    env_overlay_array = np.clip(env_energy * SOURCE_ENV_PROXY_GAIN, 0.0, 1.0)
    env_overlay = Image.fromarray(np.uint8(np.round(env_overlay_array * 255.0)), "RGB")
    env_overlay = env_overlay.filter(ImageFilter.GaussianBlur(filter_radius))
    spec_luminance = np.clip(spec_energy @ weights, 0.0, 1.0)
    spec_mean_luminance = float(spec_luminance.mean())
    env_response_array = np.asarray(env_response_image, dtype=np.float32) / 255.0
    spec_response_array = np.maximum(
        env_response_array,
        np.full_like(env_response_array, spec_mean_luminance),
    )
    spec_response_image = Image.fromarray(np.uint8(np.round(np.clip(spec_response_array, 0.0, 1.0) * 255.0)), "L")
    base_luminance = base_array @ weights
    directional = base_luminance * max(0.0, profile["light_brightness"])
    stable = (
        env_energy @ weights
        + base_luminance * max(0.0, profile["diffuse_boost"])
        + max(0.0, profile["ambient_light_color"])
    )
    stability = stable / np.maximum(stable + directional, 1e-6)
    source_lit_fraction = max(
        SOURCE_MIN_LIT_FRACTION,
        min(SOURCE_MAX_LIT_FRACTION, profile["light_brightness"] * SOURCE_LIGHT_INFLUENCE_SCALE),
    )
    lightwarp_floor = 1.0 - source_lit_fraction
    gradient = np.linspace(lightwarp_floor, 1.0, 256, dtype=np.float32)
    lightwarp_array = np.repeat(gradient[None, :, None], 16, axis=0).repeat(3, axis=2)
    lightwarp = Image.fromarray(np.uint8(np.round(lightwarp_array * 255.0)), "RGB")
    spec_mean = spec_energy.mean(axis=(0, 1))
    env_mean = env_energy.mean(axis=(0, 1))
    combined_mean = spec_mean + env_mean
    tint_peak = float(np.max(spec_mean))
    tint = spec_mean / tint_peak if tint_peak > 0.0 else np.ones(3, dtype=np.float32)
    tint_luminance = float(tint @ weights)
    boost = max(0.5, min(8.0, SOURCE_PROXY_GAIN / max(0.25, tint_luminance)))
    profile["source_phong_boost"] = round(boost, 3)
    profile["source_phong_tint"] = [round(float(value), 3) for value in tint]
    profile["source_phong_fresnel_ranges"] = [1.0, 1.0, 1.0]
    profile["source_lit_fraction"] = round(source_lit_fraction, 4)
    profile["source_lightwarp_floor"] = round(lightwarp_floor, 4)
    profile["source_emissive_strength"] = round(1.0 - source_lit_fraction, 4)
    profile["source_stability_mean"] = round(float(stability.mean()), 4)
    rgba = base.copy()
    rgba.putalpha(spec_response_image)
    response_rgb = Image.merge("RGB", (spec_response_image,) * 3)
    return rgba, response_rgb, lightwarp, env_overlay, {
        "cube_representative_rgb": [round(float(value), 4) for value in cube_rgb],
        "specular_energy_mean_rgb": [round(float(value), 4) for value in spec_mean],
        "environment_energy_mean_rgb": [round(float(value), 4) for value in env_mean],
        "combined_energy_mean_rgb": [round(float(value), 4) for value in combined_mean],
        "source_proxy_gain": SOURCE_PROXY_GAIN,
        "source_env_proxy_gain": SOURCE_ENV_PROXY_GAIN,
        "source_light_influence_scale": SOURCE_LIGHT_INFLUENCE_SCALE,
        "source_lit_fraction": round(source_lit_fraction, 4),
        "source_lightwarp_floor": round(lightwarp_floor, 4),
        "filter": "gaussian",
        "filter_radius": filter_radius,
        "phong_combination": "luma(specular_rgb_x_alpha_g)",
        "stability_combination": "stable_environment_divided_by_stable_plus_directional_diffuse",
        "lightwarp": "256x16 neutral ramp; floor=1-source_lit_fraction",
    }


def vertexlit_vmt(
    material_root: str,
    base_name: str,
    normal_name: str,
    lightwarp_name: str,
    env_overlay_name: str,
    env_dummy_name: str,
    profile: dict,
) -> str:
    exponent = profile["source_phong_exponent"]
    boost = profile["source_phong_boost"]
    strength = profile["source_emissive_strength"]
    tint = " ".join(f"{value:g}" for value in profile["source_phong_tint"])
    fresnel = " ".join(f"{value:g}" for value in profile["source_phong_fresnel_ranges"])
    return f'''"VertexLitGeneric"
{{
\t"$basetexture" "{material_root}/{base_name}"
\t"$bumpmap" "{material_root}/{normal_name}"
\t"$phong" "1"
\t"$halflambert" "1"
\t"$basemapalphaphongmask" "1"
\t"$phongexponent" "{exponent}"
\t"$phongboost" "{boost:g}"
\t"$phongfresnelranges" "[{fresnel}]"
\t"$phongtint" "[{tint}]"
\t"$lightwarptexture" "{material_root}/{lightwarp_name}"
\t"$emissiveblendenabled" "1"
\t"$emissiveblendstrength" "{strength:g}"
\t"$emissiveblendtexture" "{material_root}/{env_dummy_name}"
\t"$emissiveblendbasetexture" "{material_root}/{env_overlay_name}"
\t"$emissiveblendflowtexture" "{material_root}/{env_dummy_name}"
\t"$emissiveblendtint" "[1 1 1]"
\t"$emissiveblendscrollvector" "[0 0]"
\t"$nocull" "0"
}}
'''