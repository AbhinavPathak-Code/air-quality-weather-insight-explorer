from __future__ import annotations

import math
import html as html_lib
import json
import os
import zipfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parent
CITY_AUTOCOMPLETE = components.declare_component(
    "india_city_autocomplete", path=str(ROOT / "src" / "city_autocomplete")
)
DATA = ROOT / "data" / "raw" / "air_quality_weather_daily.csv"
OPEN_METEO_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_WEATHER = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPENAQ = "https://api.openaq.org/v3"

load_dotenv(ROOT / ".env")
st.set_page_config(
    page_title="Global Air & Weather Explorer", page_icon="🌍", layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --app-accent:#087f8c; --app-border:color-mix(in srgb,var(--text-color,#18324a) 16%,transparent); }
    /* Let Streamlit own the app and sidebar surfaces so its Light/Dark menu can switch them. */
    [data-testid="stHeader"] { background:var(--background-color,transparent); }
    [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapsedControl"] button { background:#1b2632 !important; border:1px solid #425365 !important; border-radius:10px !important; color:#edf4fb !important; }
    [data-testid="stSidebarCollapsedControl"] svg, [data-testid="stSidebarCollapsedControl"] button svg { fill:#edf4fb !important; color:#edf4fb !important; }
    [data-testid="stSidebar"] { border-right:1px solid var(--app-border); }
    h1,h2,h3 { letter-spacing:-.025em; }
    [data-testid="stMetric"] { background:rgba(120,150,180,.08); border:1px solid var(--app-border); border-radius:16px; padding:16px 18px; box-shadow:0 5px 20px rgba(30,70,100,.045); }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] { opacity:1 !important; }
    [data-testid="stMetricValue"] { font-size:1.8rem; font-weight:700; }
    [data-testid="stMetric"] { min-height:115px; transition:transform .18s ease,box-shadow .18s ease; }
    [data-testid="stMetric"]:hover { transform:translateY(-2px);box-shadow:0 10px 26px rgba(30,70,100,.1); }
    .section-intro { margin:-.45rem 0 1rem;opacity:.75;font-size:.94rem; }
    .day-card,.hour-card,.detail-card { height:100%;border:1px solid var(--app-border);border-radius:16px;background:rgba(120,150,180,.075);padding:13px 11px; }
    .day-card { min-height:155px;text-align:center; }
    .day-name { font-size:.78rem;font-weight:750;letter-spacing:.05em;text-transform:uppercase;opacity:.75; }
    .day-icon { display:inline-block;font-size:2rem;line-height:1.25;margin:5px 0;filter:drop-shadow(0 4px 5px rgba(40,70,100,.15));animation:forecast-icon-float 3s ease-in-out infinite; }
    .day-condition { min-height:2.1em;font-size:.76rem;opacity:.82; }
    .day-highlow { margin-top:5px;font-size:.92rem;font-weight:700;white-space:nowrap; }
    .day-highlow span { margin-left:5px;font-weight:500;opacity:.62; }
    .day-rain { margin-top:3px;font-size:.74rem;color:#2994c7; }
    .hour-card { min-height:118px;text-align:center;padding:10px 7px; }
    .hour-time { font-size:.76rem;font-weight:700;opacity:.75; }
    .hour-icon { display:inline-block;font-size:1.55rem;margin:5px 0;animation:forecast-icon-float 2.6s ease-in-out infinite; }
    .hour-temp { font-weight:750;font-size:.96rem; }
    .hour-rain { margin-top:3px;color:#2994c7;font-size:.72rem; }
    .detail-card { min-height:150px;padding:14px 16px; }
    .detail-label { font-size:.78rem;opacity:.72; }
    .detail-value { margin-top:6px;font-size:1.15rem;font-weight:750; }
    .weather-details-intro { margin:-.45rem 0 1rem;opacity:.72;font-size:.92rem; }
    .weather-detail-card { position:relative;height:calc(100% - 12px);min-height:150px;margin:3px 4px 15px;padding:17px 18px;border:1px solid var(--app-border);border-radius:19px;background:linear-gradient(145deg,rgba(120,150,180,.13),rgba(120,150,180,.05));box-shadow:0 8px 22px rgba(25,50,80,.07);overflow:hidden;transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease;transform-style:preserve-3d; }
    .weather-detail-card:hover { z-index:3;transform:perspective(900px) translateY(-5px) scale(1.018);border-color:rgba(61,170,205,.58);box-shadow:0 18px 34px rgba(20,60,90,.2); }
    .wind-compass-card { display:flex;align-items:center;gap:20px; }
    .wind-compass { position:relative;flex:0 0 116px;width:116px;height:116px;border:1px solid rgba(120,160,200,.3);border-radius:50%;background:radial-gradient(circle,rgba(80,135,185,.1) 0 49%,transparent 50%),repeating-conic-gradient(from 0deg,rgba(120,160,200,.5) 0deg 1deg,transparent 1deg 8deg);box-shadow:inset 0 0 0 7px rgba(120,160,200,.06),0 6px 18px rgba(40,80,120,.1); }
    .wind-compass::before { content:"";position:absolute;inset:11px;border:1px solid rgba(120,160,200,.25);border-radius:50%; }
    .compass-label { position:absolute;z-index:2;font-size:.66rem;font-weight:800;opacity:.7; }
    .compass-n { top:4px;left:50%;transform:translateX(-50%);color:#f06a7b; }.compass-e {right:5px;top:50%;transform:translateY(-50%)}.compass-s {bottom:4px;left:50%;transform:translateX(-50%)}.compass-w {left:5px;top:50%;transform:translateY(-50%)}
    .compass-needle { position:absolute;z-index:3;left:calc(50% - 2px);top:24px;width:4px;height:68px;transform-origin:50% 50%;transition:transform 1s cubic-bezier(.2,.8,.2,1); }
    .compass-needle::before { content:"";position:absolute;top:0;left:-5px;border-left:7px solid transparent;border-right:7px solid transparent;border-bottom:33px solid #ff647b;filter:drop-shadow(0 2px 3px rgba(200,50,80,.25)); }
    .compass-needle::after { content:"";position:absolute;top:32px;left:0;width:4px;height:31px;border-radius:0 0 5px 5px;background:#6f91b4; }
    .compass-hub { position:absolute;z-index:4;left:calc(50% - 5px);top:calc(50% - 5px);width:10px;height:10px;border:2px solid #fff;border-radius:50%;background:#ff647b;box-shadow:0 0 0 4px rgba(255,100,123,.15); }
    .wind-info { min-width:0;flex:1; }.wind-info .detail-label { letter-spacing:.08em;text-transform:uppercase; }
    .wind-bearing { margin-top:5px;font-size:1.35rem;font-weight:800; }.wind-speed {margin-top:3px;font-size:1.08rem;font-weight:750;}
    .wind-speed small {font-size:.78rem;font-weight:600;opacity:.7;}
    .wind-lines { display:flex;gap:4px;margin-top:12px;align-items:center;height:13px; }
    .wind-lines i {display:block;height:2px;border-radius:4px;background:linear-gradient(90deg,#59c7e8,transparent);animation:breeze var(--breeze-duration,1.4s) ease-in-out infinite;}
    .wind-lines i:nth-child(1){width:34px}.wind-lines i:nth-child(2){width:22px;animation-delay:.2s}.wind-lines i:nth-child(3){width:28px;animation-delay:.4s}
    @keyframes breeze {0%,100%{transform:translateX(-3px);opacity:.4}50%{transform:translateX(7px);opacity:1}}
    .detail-big { margin-top:8px;font-size:1.55rem;font-weight:800;letter-spacing:-.03em; }
    .detail-big small {font-size:.8rem;font-weight:650;letter-spacing:0;opacity:.72;}
    .detail-sub { margin-top:7px;font-size:.76rem;opacity:.72; }
    .detail-progress { height:7px;margin-top:12px;border-radius:999px;background:rgba(120,145,170,.18);overflow:hidden; }
    .detail-progress span { display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,#43bd83,#ffd34f,#fa884b,#db4d7a);transition:width .7s ease; }
    .uv-risk { display:inline-flex;margin-left:7px;padding:3px 8px;border-radius:999px;background:rgba(70,165,110,.15);color:#25945f;font-size:.68rem;font-weight:750;vertical-align:middle; }
    .pressure-dial { display:inline-flex;width:27px;height:27px;margin-top:8px;align-items:center;justify-content:center;border:2px dashed rgba(76,150,205,.65);border-radius:50%;color:#4c96cd;font-size:.85rem;animation:pressure-turn 12s linear infinite; }
    @keyframes pressure-turn {to{transform:rotate(360deg)}}
    .aqi-pill { display:inline-flex;align-items:center;margin-top:7px;padding:4px 9px;border-radius:999px;font-size:.73rem;font-weight:750;background:rgba(28,160,104,.15);color:#158354; }
    @media(max-width:780px){.day-card{min-height:140px;padding:10px 5px}.day-condition{font-size:.68rem}.day-highlow{font-size:.8rem}.hour-card{min-height:105px}}
    [data-testid="stTabs"] button[aria-selected="true"] { color:var(--primary-color,var(--app-accent)) !important; }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] { background:var(--primary-color,var(--app-accent)) !important; border-color:var(--primary-color,var(--app-accent)) !important; color:#fff !important; }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] *, [data-testid="stBaseButton-primary"] * { color:#fff !important; }
    [data-testid="stTextInput"] input { border:1px solid var(--app-border) !important; border-radius:13px !important; box-shadow:0 3px 0 rgba(90,120,150,.15),0 8px 18px rgba(30,70,100,.08) !important; min-height:48px; }
    [data-testid="stTextInput"] input:focus { border-color:var(--primary-color,var(--app-accent)) !important; box-shadow:0 0 0 3px color-mix(in srgb,var(--primary-color,var(--app-accent)) 20%,transparent),0 7px 16px rgba(30,70,100,.1) !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div { border:1px solid var(--app-border) !important; border-radius:12px !important; }
    [role="listbox"] { border:1px solid var(--app-border) !important; border-radius:12px !important; box-shadow:0 12px 28px rgba(20,40,60,.18) !important; }
    .search-heading { display:flex;align-items:center;justify-content:space-between;font-size:1.12rem;font-weight:750;margin:.2rem 0 1rem;min-height:64px; }
    .search-weather-icon { position:relative;display:inline-block;width:86px;height:62px;filter:drop-shadow(0 5px 7px rgba(50,100,140,.2)); }
    .side-sun { position:absolute;right:20px;top:2px;width:40px;height:40px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff5a9 0 10%,#ffd34f 38%,#ff923e 78%);box-shadow:0 0 0 6px rgba(255,198,68,.13),0 0 22px rgba(255,183,62,.42);animation:sun-pulse 2.8s ease-in-out infinite; }
    .side-cloud { position:absolute;left:5px;bottom:6px;width:60px;height:24px;border-radius:24px;background:linear-gradient(180deg,#fff 0%,#e9efff 60%,#c7d5f1 100%);box-shadow:inset 0 -3px 5px rgba(101,125,175,.2);animation:cloud-drift 3.5s ease-in-out infinite; }
    .side-cloud::before,.side-cloud::after { content:"";position:absolute;bottom:8px;border-radius:50%;background:inherit; }
    .side-cloud::before { left:9px;width:28px;height:28px; }.side-cloud::after { left:28px;bottom:10px;width:25px;height:25px; }
    .hero { position:relative;isolation:isolate;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:22px;min-height:270px;background:linear-gradient(120deg,rgba(38,138,166,.18),rgba(112,152,193,.13));border:1px solid var(--app-border);border-radius:24px;padding:24px 30px;margin:4px 0 18px; }
    .hero::before { content:"";position:absolute;z-index:0;pointer-events:none;inset:0;background:radial-gradient(ellipse at 82% 18%,rgba(255,255,255,.16),transparent 36%),radial-gradient(ellipse at 17% 92%,rgba(255,255,255,.09),transparent 40%);animation:sky-drift 18s ease-in-out infinite alternate; }
    .hero.weather-sunny { background:linear-gradient(120deg,rgba(247,183,75,.24),rgba(49,165,192,.13)); }
    .hero.weather-dawn { background:linear-gradient(120deg,rgba(255,173,102,.27),rgba(178,145,206,.16),rgba(74,137,190,.14)); }
    .hero.weather-dusk { background:linear-gradient(120deg,rgba(230,119,104,.24),rgba(116,104,168,.19),rgba(49,94,153,.15)); }
    .hero.weather-night { background:linear-gradient(120deg,rgba(21,37,75,.96),rgba(34,54,101,.91) 52%,rgba(38,88,119,.88)); }
    .hero.weather-night .hero-content,.hero.weather-night .hero-dog { color:#f6f8ff; }
    .hero.weather-night::before { background-image:radial-gradient(circle at 12% 28%,rgba(255,255,255,.72) 0 1px,transparent 1.8px),radial-gradient(circle at 39% 19%,rgba(255,255,255,.58) 0 1px,transparent 1.8px),radial-gradient(circle at 72% 24%,rgba(255,255,255,.62) 0 1px,transparent 1.8px),radial-gradient(circle at 91% 58%,rgba(255,255,255,.5) 0 1px,transparent 1.8px);background-size:100% 100%; }
    .hero.weather-night::after { content:"";position:absolute;z-index:0;pointer-events:none;left:-2%;right:-2%;bottom:-1px;height:54px;background:linear-gradient(180deg,rgba(9,20,40,.35),rgba(7,17,33,.68));clip-path:polygon(0 65%,8% 46%,15% 62%,24% 35%,31% 67%,43% 42%,54% 69%,64% 39%,74% 64%,82% 35%,91% 61%,100% 43%,100% 100%,0 100%); }
    .hero.weather-rain { background:linear-gradient(120deg,rgba(57,114,165,.25),rgba(105,139,175,.18)); }
    .hero.weather-storm { background:linear-gradient(120deg,rgba(52,66,98,.38),rgba(84,90,124,.27));animation:storm-glow 5s ease-in-out infinite; }
    .hero-content { position:relative;z-index:1;flex:1;min-width:0; }
    .hero-title { font-size:1.08rem; margin:0; opacity:.82;letter-spacing:.08em; }
    .hero-time { margin:.2rem 0 .35rem;opacity:.78;font-size:.88rem;font-weight:600; }
    .hero-city { font-size:2.3rem; font-weight:750; margin:.15rem 0; }
    .hero-cityrow { display:flex;align-items:baseline;flex-wrap:wrap;gap:18px;margin:.1rem 0 .35rem; }
    .hero-cityrow .hero-city { margin:0; }
    .hero-current-temp { font-size:2rem;font-weight:800;letter-spacing:-.04em; }
    .hero-current-temp span { margin-left:4px;font-size:1.15rem;font-weight:700;opacity:.82; }
    .hero-note { display:flex;align-items:center;flex-wrap:wrap;gap:9px;margin:0;opacity:.92;font-size:1.02rem; }
    .hero-condition { display:inline-flex;padding:4px 10px;border:1px solid rgba(255,255,255,.24);border-radius:999px;background:rgba(255,255,255,.13);font-size:.86rem;font-weight:700; }
    .weather-scene { position:relative;display:flex;align-items:center;gap:14px;font-size:5.4rem;line-height:1;min-height:128px;filter:drop-shadow(0 12px 10px rgba(30,50,80,.18)); }
    .weather-art { position:relative;display:block;width:164px;height:128px;flex:0 0 164px; }
    .sun-core { position:absolute;left:35px;top:15px;width:78px;height:78px;border-radius:50%;background:radial-gradient(circle at 32% 28%,#fff6b6 0 8%,#ffd84f 35%,#ffb52f 65%,#ff8e38 100%);box-shadow:0 0 0 9px rgba(255,195,60,.13),0 0 36px rgba(255,177,55,.35);animation:sun-pulse 3s ease-in-out infinite; }
    .weather-art.twilight .sun-core { left:43px;top:48px;width:68px;height:68px;clip-path:inset(0 0 48% 0); }
    .sun-horizon { position:absolute;left:12px;right:5px;bottom:25px;height:3px;border-radius:4px;background:linear-gradient(90deg,transparent,rgba(255,250,235,.88),transparent);box-shadow:0 0 18px rgba(255,206,128,.65); }
    .moon-symbol { position:absolute;left:38px;top:-3px;font-size:7rem;line-height:1;color:#eaf2ff;text-shadow:0 0 25px rgba(183,208,255,.65);animation:moon-float 4.2s ease-in-out infinite; }
    .weather-art.night::before { content:"✦  ·     ·  ✧";position:absolute;inset:8px 0 auto 0;color:rgba(255,255,255,.85);font-size:1.1rem;letter-spacing:1rem;animation:star-twinkle 2.5s ease-in-out infinite alternate; }
    .cloud-shape { position:absolute;left:22px;top:47px;width:112px;height:43px;border-radius:36px;background:linear-gradient(180deg,#fff 0%,#edf4ff 55%,#b9c9e7 100%);box-shadow:inset 0 -5px 8px rgba(73,102,158,.16),0 8px 18px rgba(31,54,94,.14);animation:cloud-drift 4.5s ease-in-out infinite; }
    .cloud-shape::before,.cloud-shape::after { content:"";position:absolute;bottom:13px;border-radius:50%;background:linear-gradient(180deg,#fff 0%,#edf4ff 56%,#c4d2eb 100%); }
    .cloud-shape::before { left:17px;width:49px;height:49px; }.cloud-shape::after { left:51px;bottom:16px;width:42px;height:42px; }
    .weather-art.partly .sun-core { left:16px;top:12px;width:72px;height:72px; }
    .weather-art.partly .cloud-shape { left:46px;top:58px;transform:scale(.82); }
    .weather-art.rainy .cloud-shape,.weather-art.stormy .cloud-shape,.weather-art.snowy .cloud-shape { left:17px;top:31px; }
    .rain-drops { position:absolute;left:47px;top:81px;color:#8bd8ff;font-size:1.55rem;letter-spacing:.45rem;animation:rain-fall .9s linear infinite; }
    .storm-bolt { position:absolute;left:85px;top:75px;font-size:2.6rem;color:#ffd95e;filter:drop-shadow(0 0 10px #ffbc46);animation:flash 1.1s steps(2,end) infinite; }
    .snow-flakes { position:absolute;left:45px;top:79px;color:#e9f8ff;font-size:1.4rem;letter-spacing:.55rem;animation:rain-fall 1.6s linear infinite; }
    .fog-lines { position:absolute;left:17px;top:98px;width:122px;height:3px;background:rgba(229,241,255,.78);border-radius:4px;box-shadow:12px 11px 0 rgba(229,241,255,.5),-6px 22px 0 rgba(229,241,255,.35);animation:cloud-drift 4s ease-in-out infinite alternate; }
    .weather-scene.night .weather-art { filter:drop-shadow(0 0 15px rgba(199,216,255,.3)); }
    @keyframes drift { 0%,100%{transform:translateY(0) rotate(-2deg)} 50%{transform:translateY(-9px) rotate(2deg)} }
    @keyframes forecast-icon-float { 0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)} }
    @keyframes sky-drift { from{transform:translateX(-2%) translateY(1%)}to{transform:translateX(3%) translateY(-2%)} }
    @keyframes storm-glow { 0%,90%,100%{filter:none}92%,96%{filter:brightness(1.35)} }
    @keyframes cloud-drift { 0%,100%{transform:translateX(0) translateY(0)} 50%{transform:translateX(10px) translateY(-4px)} }
    @keyframes sun-pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.08)} }
    @keyframes storm-bob { 0%,100%{transform:translateY(0)} 50%{transform:translateY(4px)} }
    @keyframes moon-float { 0%,100%{transform:translateY(2px) rotate(-3deg)}50%{transform:translateY(-7px) rotate(3deg)} }
    @keyframes star-twinkle { from{opacity:.45;transform:translateY(0)}to{opacity:1;transform:translateY(-3px)} }
    @keyframes rain-fall { 0%{transform:translateY(-3px);opacity:.45} 100%{transform:translateY(6px);opacity:1} }
    @keyframes flash { 0%,48%,100%{opacity:.25} 49%,70%{opacity:1;filter:drop-shadow(0 0 9px #ffca55)} }
    .buddy { display:flex; align-items:center; gap:14px; background:rgba(120,150,180,.08); border:1px solid var(--app-border); border-radius:18px; padding:15px 18px; margin:10px 0 16px; }
    .dog-figure { width:90px;height:78px;flex:0 0 90px;overflow:visible;filter:drop-shadow(0 8px 8px rgba(30,45,70,.2)); }
    .dog-figure.happy { animation:dog-bob 2.4s ease-in-out infinite; }
    .dog-figure.sad { animation:dog-bob 3.5s ease-in-out infinite; }
    @keyframes dog-bob { 0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-3px) scale(1.015)} }
    .hero-dog { position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;min-width:145px;padding:12px 16px;border:1px solid rgba(255,255,255,.27);border-radius:20px;background:rgba(255,255,255,.16);backdrop-filter:blur(8px); }
    .hero-dog .dog-figure { width:158px;height:132px;flex-basis:132px; }
    .hero-dog-label { font-weight:750;text-align:center;font-size:.9rem; }
    .hero-dog-note { font-size:.74rem;opacity:.84;text-align:center;max-width:160px; }
    .dog-mask { animation:mask-breathe 2s ease-in-out infinite; }
    .dog-tail { transform-box:fill-box;transform-origin:15% 50%;animation:tail-wag .42s ease-in-out infinite alternate; }
    .dog-head { transform-box:fill-box;transform-origin:50% 75%;animation:head-shake 1.15s ease-in-out infinite; }
    .dog-eyes { transform-box:fill-box;transform-origin:center;animation:dog-blink 5.4s ease-in-out infinite; }
    .dog-ear-left,.dog-ear-right { transform-box:fill-box;transform-origin:50% 90%;animation:ear-bounce 2.4s ease-in-out infinite; }
    .dog-figure.sad .dog-tail { animation:tail-slow 1.5s ease-in-out infinite alternate; }
    .dog-figure.sad .dog-head { animation:head-droop 2.4s ease-in-out infinite; }
    @keyframes tail-wag { from{transform:rotate(-25deg)}to{transform:rotate(25deg)} }
    @keyframes tail-slow { from{transform:rotate(-7deg)}to{transform:rotate(9deg)} }
    @keyframes head-shake { 0%,100%{transform:rotate(0)}25%{transform:rotate(-5deg)}75%{transform:rotate(5deg)} }
    @keyframes head-droop { 0%,100%{transform:rotate(5deg) translateY(1px)}50%{transform:rotate(9deg) translateY(3px)} }
    @keyframes mask-breathe { 0%,100%{transform:scaleY(1)}50%{transform:scaleY(.92)} }
    @keyframes dog-blink { 0%,45%,49%,100%{transform:scaleY(1)}47%{transform:scaleY(.12)} }
    @keyframes ear-bounce { 0%,100%{transform:rotate(0)}50%{transform:rotate(3deg)} }
    @media(max-width:700px){.hero{min-height:220px;padding:20px;gap:8px}.weather-scene{font-size:4rem;min-height:85px}.weather-art{transform:scale(.78);transform-origin:left center;width:130px;flex-basis:130px}.hero-city{font-size:1.8rem}.hero-dog{min-width:100px;padding:8px}.hero-dog .dog-figure{width:108px;height:94px;flex-basis:94px}.hero-dog-note{max-width:110px}}
    @media(max-width:900px){.wind-compass-card{gap:12px}.wind-compass{transform:scale(.86);transform-origin:left center;margin-right:-12px}}
    @media(max-width:700px){.weather-detail-card{min-height:130px;padding:12px;margin:2px 2px 12px}.wind-compass{transform:scale(.75);margin-right:-25px}.wind-bearing{font-size:1.08rem}}
    @media(prefers-reduced-motion:reduce){.hero::before,.hero.weather-storm,.weather-art,.sun-core,.moon-symbol,.cloud-shape,.rain-drops,.storm-bolt,.snow-flakes,.fog-lines,.side-sun,.side-cloud,.day-icon,.hour-icon,.dog-tail,.dog-head,.dog-mask,.dog-eyes,.dog-ear-left,.dog-ear-right,.dog-figure.happy,.dog-figure.sad,.wind-lines i,.pressure-dial,.weather-detail-card{animation:none!important;transition:none!important}}
    .buddy-title { font-weight:700; }
    .buddy-copy { font-size:.92rem; opacity:.9; }
    .small-note { font-size:.88rem; opacity:.9; }
    div.stButton > button { border-radius:11px; border:1px solid #b8d5e5; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_json(url: str, *, params: dict | None = None, headers: dict | None = None) -> dict:
    response = requests.get(url, params=params, headers=headers, timeout=35)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60 * 60)
def search_city(name: str, country_code: str | None = None) -> list[dict]:
    params = {"name": name, "count": 8, "language": "en"}
    if country_code:
        params["countryCode"] = country_code
    payload = get_json(OPEN_METEO_GEOCODING, params=params)
    return payload.get("results", [])


@st.cache_data(ttl=15 * 60)
def get_weather(latitude: float, longitude: float, temperature_unit: str = "celsius") -> dict:
    return get_json(OPEN_METEO_WEATHER, params={
        "latitude": latitude, "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m,cloud_cover,pressure_msl,visibility,uv_index",
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,sunrise,sunset",
        "forecast_days": 7, "timezone": "auto", "temperature_unit": temperature_unit,
    })


@st.cache_data(ttl=15 * 60)
def get_air_forecast(latitude: float, longitude: float) -> dict:
    return get_json(OPEN_METEO_AIR, params={
        "latitude": latitude, "longitude": longitude,
        "current": "pm2_5,pm10,us_aqi,european_aqi",
        "hourly": "pm2_5,pm10,nitrogen_dioxide,ozone,sulphur_dioxide,carbon_monoxide,us_aqi",
        "forecast_days": 5, "timezone": "auto",
    })


@st.cache_data(ttl=30 * 60)
def nearby_openaq_stations(latitude: float, longitude: float, radius_km: int, api_key: str) -> list[dict]:
    payload = get_json(
        f"{OPENAQ}/locations",
        params={"coordinates": f"{latitude},{longitude}", "radius": radius_km * 1000,
                "limit": 100},
        headers={"X-API-Key": api_key},
    )
    locations = payload.get("results", [])
    for location in locations:
        coords = location.get("coordinates") or {}
        lat, lon = coords.get("latitude"), coords.get("longitude")
        if lat is None or lon is None:
            location["distance_km"] = None
        else:
            lat1, lon1, lat2, lon2 = map(math.radians, [latitude, longitude, lat, lon])
            dlat, dlon = lat2 - lat1, lon2 - lon1
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            location["distance_km"] = 6371 * 2 * math.asin(math.sqrt(a))
    return sorted(locations, key=lambda item: item.get("distance_km") or 999999)


@st.cache_data(ttl=5 * 60)
def get_latest_station_readings(location_id: int, api_key: str) -> list[dict]:
    payload = get_json(
        f"{OPENAQ}/locations/{location_id}/latest", params={"limit": 100},
        headers={"X-API-Key": api_key},
    )
    return payload.get("results", [])


def day_phase(value) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return "day"
    hour = timestamp.hour
    if hour < 5 or hour >= 20:
        return "night"
    if 5 <= hour < 8:
        return "dawn"
    if 17 <= hour < 20:
        return "dusk"
    return "day"


def weather_description(code: int | None, local_time=None) -> tuple[str, str]:
    phase = day_phase(local_time)
    if code is None or pd.isna(code):
        return "Weather", "🌤️"
    code = int(code)
    if code == 0:
        return "Clear sky", {"night": "🌙", "dawn": "🌅", "dusk": "🌄"}.get(phase, "☀️")
    if code in (1, 2):
        return "Partly cloudy", {"night": "🌙☁️", "dawn": "🌤️", "dusk": "🌥️"}.get(phase, "🌤️")
    if code == 3:
        return "Overcast", "☁️"
    if code in (45, 48):
        return "Foggy", "🌫️"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "Rain showers", "🌧️"
    if code in (71, 73, 75, 77, 85, 86):
        return "Snow", "🌨️"
    if code in (95, 96, 99):
        return "Thunderstorm", "☁️"
    return "Cloudy", "☁️"


def weather_illustration(code: int | None, local_time=None) -> str:
    """Create a small animated CSS scene matched to the local hour and weather code."""
    phase = day_phase(local_time)
    if code is None or pd.isna(code):
        return '<span class="weather-art partly"><span class="sun-core"></span><span class="cloud-shape"></span></span>'
    code = int(code)
    if code in (95, 96, 99):
        return '<span class="weather-art stormy"><span class="cloud-shape"></span><span class="storm-bolt">ϟ</span></span>'
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return '<span class="weather-art rainy"><span class="cloud-shape"></span><span class="rain-drops">• • •</span></span>'
    if code in (71, 73, 75, 77, 85, 86):
        return '<span class="weather-art snowy"><span class="cloud-shape"></span><span class="snow-flakes">✳ ✳</span></span>'
    if code in (45, 48):
        return '<span class="weather-art foggy"><span class="cloud-shape"></span><span class="fog-lines"></span></span>'
    if code == 3:
        return '<span class="weather-art overcast"><span class="cloud-shape"></span></span>'
    if code in (1, 2):
        if phase == "night":
            return '<span class="weather-art night partly"><span class="moon-symbol">☾</span><span class="cloud-shape"></span></span>'
        return '<span class="weather-art partly"><span class="sun-core"></span><span class="cloud-shape"></span></span>'
    if phase == "night":
        return '<span class="weather-art night"><span class="moon-symbol">☾</span></span>'
    if phase in ("dawn", "dusk"):
        return '<span class="weather-art twilight"><span class="sun-core"></span><span class="sun-horizon"></span></span>'
    return '<span class="weather-art clear"><span class="sun-core"></span></span>'


def display_day_card(day: str, condition: str, icon: str, high, low, rain, temp_unit: str) -> str:
    high_text = f"{float(high):.0f}{temp_unit}" if high is not None and not pd.isna(high) else "—"
    low_text = f"{float(low):.0f}{temp_unit}" if low is not None and not pd.isna(low) else "—"
    rain_text = f"☂ {float(rain):.0f}%" if rain is not None and not pd.isna(rain) else ""
    return (
        f'<div class="day-card"><div class="day-name">{day}</div><div class="day-icon">{icon}</div>'
        f'<div class="day-condition">{condition}</div><div class="day-highlow">{high_text}<span>{low_text}</span></div>'
        f'<div class="day-rain">{rain_text}</div></div>'
    )


def display_hour_card(time_label: str, condition: str, icon: str, temperature, rain, temp_unit: str) -> str:
    temp_text = f"{float(temperature):.0f}{temp_unit}" if temperature is not None and not pd.isna(temperature) else "—"
    rain_text = f"☂ {float(rain):.0f}%" if rain is not None and not pd.isna(rain) else ""
    return (
        f'<div class="hour-card"><div class="hour-time">{time_label}</div>'
        f'<div class="hour-icon" title="{condition}">{icon}</div><div class="hour-temp">{temp_text}</div>'
        f'<div class="hour-rain">{rain_text}</div></div>'
    )


def display_detail_card(label: str, value: str, note: str = "") -> str:
    note_html = f'<div class="detail-sub">{note}</div>' if note else ""
    return f'<div class="detail-card"><div class="detail-label">{label}</div><div class="detail-value">{value}</div>{note_html}</div>'


def compass_direction(degrees) -> str:
    if degrees is None or pd.isna(degrees):
        return "—"
    points = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")
    return points[int((float(degrees) % 360 + 11.25) // 22.5) % 16]


def wind_compass_card(degrees, speed, speed_unit: str) -> str:
    valid_direction = degrees is not None and not pd.isna(degrees)
    bearing = float(degrees) % 360 if valid_direction else 0
    direction = compass_direction(degrees)
    speed_text = f"{float(speed):.1f}" if speed is not None and not pd.isna(speed) else "—"
    bearing_text = f"{bearing:.0f}°" if valid_direction else "—"
    wind_value = float(speed) if speed is not None and not pd.isna(speed) else 0
    breeze_duration = max(.55, min(2.2, 2.2 / (1 + wind_value / 12)))
    return (
        '<div class="weather-detail-card wind-compass-card"><div class="wind-compass" role="img" '
        f'aria-label="Wind direction {direction}, {bearing_text}"><span class="compass-label compass-n">N</span>'
        '<span class="compass-label compass-e">E</span><span class="compass-label compass-s">S</span>'
        '<span class="compass-label compass-w">W</span>'
        f'<span class="compass-needle" style="transform:rotate({bearing:.1f}deg);opacity:{1 if valid_direction else .25}"></span>'
        '<span class="compass-hub"></span></div><div class="wind-info">'
        '<div class="detail-label">Wind direction · selected city</div>'
        f'<div class="wind-bearing">From {direction} <small>{bearing_text}</small></div>'
        f'<div class="wind-speed">{speed_text} <small>{speed_unit} wind speed</small></div>'
        f'<div class="wind-lines" style="--breeze-duration:{breeze_duration:.2f}s" aria-hidden="true"><i></i><i></i><i></i></div></div></div>'
    )


def gust_detail_card(speed, speed_unit: str) -> str:
    speed_value = float(speed) if speed is not None and not pd.isna(speed) else None
    speed_text = f"{speed_value:.1f}" if speed_value is not None else "—"
    breeze_duration = max(.55, min(2.2, 2.2 / (1 + (speed_value or 0) / 12)))
    return (
        '<div class="weather-detail-card"><div class="detail-label">Wind gust · past hour</div>'
        f'<div class="detail-big">{speed_text} <small>{speed_unit}</small></div>'
        f'<div class="wind-lines" style="--breeze-duration:{breeze_duration:.2f}s" aria-hidden="true"><i></i><i></i><i></i></div>'
        '<div class="detail-sub">Peak modelled gust during the last hour</div></div>'
    )


def progress_detail_card(label: str, value, unit: str, percent: float, note: str) -> str:
    value_text = f"{float(value):.0f}" if value is not None and not pd.isna(value) else "—"
    width = max(0, min(100, float(percent)))
    return (
        f'<div class="weather-detail-card"><div class="detail-label">{label}</div>'
        f'<div class="detail-big">{value_text} <small>{unit}</small></div>'
        f'<div class="detail-progress"><span style="width:{width:.0f}%"></span></div>'
        f'<div class="detail-sub">{note}</div></div>'
    )


def uv_detail_card(value) -> str:
    uv = float(value) if value is not None and not pd.isna(value) else None
    risk = "—" if uv is None else "Low" if uv < 3 else "Moderate" if uv < 6 else "High" if uv < 8 else "Very high" if uv < 11 else "Extreme"
    percent = max(0, min(100, uv / 11 * 100)) if uv is not None else 0
    value_text = f"{uv:.1f}" if uv is not None else "—"
    return (
        f'<div class="weather-detail-card"><div class="detail-label">UV index</div>'
        f'<div class="detail-big">{value_text}<span class="uv-risk">{risk}</span></div>'
        f'<div class="detail-progress"><span style="width:{percent:.0f}%"></span></div>'
        '<div class="detail-sub">Model estimate for the selected city</div></div>'
    )


def aqi_label(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "Not available"
    value = float(value)
    if value <= 50:
        return "Good"
    if value <= 100:
        return "Moderate"
    if value <= 150:
        return "Unhealthy for sensitive groups"
    if value <= 200:
        return "Unhealthy"
    if value <= 300:
        return "Very unhealthy"
    return "Hazardous"


def smart_brief(question: str, city: str, weather: dict, air: dict) -> str:
    current_weather = weather.get("current", {})
    current_air = air.get("current", {})
    temp = current_weather.get("temperature_2m")
    pm25 = current_air.get("pm2_5")
    aqi = current_air.get("us_aqi")
    code = current_weather.get("weather_code")
    description, _ = weather_description(code)
    temp_unit = weather.get("current_units", {}).get("temperature_2m", "°C")
    parts = [f"For **{city}**, the latest model snapshot shows **{description.lower()}**"]
    if temp is not None:
        parts[-1] += f" and **{temp:.1f}{temp_unit}**"
    if pm25 is not None:
        parts.append(f"PM2.5 is estimated at **{pm25:.1f} µg/m³**")
    if aqi is not None:
        parts.append(f"with a modelled **US AQI of {int(aqi)} ({aqi_label(aqi)})**")
    elif pm25 is None:
        parts.append("but air-quality data is unavailable for this location right now")
    parts.append("These are model estimates, not a nearby monitor reading or official health advice.")
    return ". ".join(parts) + "."


def display_weather_card(city: str, region: str, weather: dict, dog_svg: str, mood: str, dog_note: str) -> None:
    current = weather.get("current", {})
    desc, _ = weather_description(current.get("weather_code"), current.get("time"))
    code = current.get("weather_code")
    if code is not None and int(code) in (95, 96, 99):
        effect_class, effect = "storm", ""
    elif code is not None and int(code) in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        effect_class, effect = "rain", ""
    elif code is not None and int(code) == 0:
        effect_class, effect = "sunny", ""
    else:
        effect_class, effect = "cloudy", ""
    phase = day_phase(current.get("time"))
    current_timestamp = pd.to_datetime(current.get("time"), errors="coerce")
    daily_weather = weather.get("daily", {})
    sunrise_values = daily_weather.get("sunrise", [])
    sunset_values = daily_weather.get("sunset", [])
    sunrise_timestamp = pd.to_datetime(sunrise_values[0], errors="coerce") if sunrise_values else pd.NaT
    sunset_timestamp = pd.to_datetime(sunset_values[0], errors="coerce") if sunset_values else pd.NaT
    if pd.notna(current_timestamp) and pd.notna(sunrise_timestamp) and pd.notna(sunset_timestamp):
        if current_timestamp < sunrise_timestamp or current_timestamp >= sunset_timestamp:
            phase = "night"
        elif (current_timestamp - sunrise_timestamp).total_seconds() < 3600:
            phase = "dawn"
        elif (sunset_timestamp - current_timestamp).total_seconds() < 3600:
            phase = "dusk"
    clear_or_partly_cloudy = code in (0, 1, 2)
    if clear_or_partly_cloudy and phase in {"night", "dawn", "dusk"}:
        hero_class = f"weather-{phase}"
    else:
        hero_class = "weather-storm" if effect_class == "storm" else "weather-rain" if effect_class == "rain" else "weather-sunny" if effect_class == "sunny" else "weather-cloudy"
    scene_class = "night" if phase == "night" and clear_or_partly_cloudy else effect_class
    timestamp = pd.to_datetime(current.get("time"), errors="coerce")
    local_clock = timestamp.strftime("%A, %d %b · %I:%M %p").replace(" 0", " ") if pd.notna(timestamp) else "Local time unavailable"
    timezone = weather.get("timezone_abbreviation") or "local time"
    temp_unit = weather.get("current_units", {}).get("temperature_2m", "°C")
    dog_path = ROOT / "assets" / "happy-dog.lottie"
    try:
        with zipfile.ZipFile(dog_path) as animation_file:
            animation_name = next(name for name in animation_file.namelist() if name.startswith("animations/") and name.endswith(".json"))
            animation_data = json.dumps(json.loads(animation_file.read(animation_name)), separators=(",", ":"))
            animation_data = animation_data.replace("<", "\\u003c")
    except (OSError, KeyError, StopIteration, zipfile.BadZipFile, json.JSONDecodeError):
        animation_data = "null"

    temperature = current.get("temperature_2m", "—")
    safe_city = html_lib.escape(str(city))
    safe_region = html_lib.escape(str(region))
    safe_temperature = html_lib.escape(str(temperature))
    safe_temp_unit = html_lib.escape(str(temp_unit))
    safe_local_clock = html_lib.escape(local_clock)
    safe_timezone = html_lib.escape(str(timezone))
    safe_description = html_lib.escape(str(desc))
    safe_mood = html_lib.escape(str(mood))
    safe_dog_note = html_lib.escape(str(dog_note))
    mood_class = "resting" if any(word in mood.lower() for word in ("cover", "shade", "mask")) else "joyful"
    mood_icon = "⛈️" if "cover" in mood.lower() else "🌡️" if "shade" in mood.lower() else "☔" if "rain" in mood.lower() else "☀️"
    mask_badge = f'<span class="mood-icon">{mood_icon}</span>'
    mask_overlay = '<span class="puppy-mask" aria-label="playful air-quality mask"></span>' if "mask" in mood.lower() else ""
    scene = weather_illustration(code, current.get("time"))
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
    *{{box-sizing:border-box}} body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#f6f8ff}}
    .hero{{position:relative;isolation:isolate;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:320px;padding:24px 30px;border:1px solid rgba(255,255,255,.13);border-radius:26px;background:linear-gradient(120deg,#17384b,#1c2b42 54%,#243144);box-shadow:0 14px 38px rgba(12,27,45,.16);transition:background .35s ease}}
    .hero::before{{content:"";position:absolute;z-index:-1;inset:-15%;pointer-events:none;background:radial-gradient(ellipse at 20% 5%,rgba(95,193,220,.24),transparent 37%),radial-gradient(ellipse at 84% 22%,rgba(208,208,255,.17),transparent 33%),radial-gradient(ellipse at 46% 108%,rgba(66,163,183,.15),transparent 45%);animation:sky 16s ease-in-out infinite alternate}}
    .hero.weather-sunny{{background:linear-gradient(120deg,#57412d,#26344b 58%,#25384a)}}.hero.weather-dawn{{background:linear-gradient(120deg,#67433d,#3d3d5b 55%,#293d54)}}.hero.weather-dusk{{background:linear-gradient(120deg,#57373e,#383653 55%,#203447)}}.hero.weather-night{{background:linear-gradient(120deg,#111e3b,#1a2b4d 55%,#1d3c55)}}.hero.weather-rain{{background:linear-gradient(120deg,#183749,#26364b 60%,#263f51)}}.hero.weather-storm{{background:linear-gradient(120deg,#242940,#2e344c 60%,#28394b);animation:glow 5s ease-in-out infinite}}
    .hero.light-theme{{color:#20344b;border-color:rgba(53,92,128,.18);box-shadow:0 16px 38px rgba(47,76,106,.13)}}
    .hero.light-theme.weather-sunny{{background:linear-gradient(118deg,#fff0c9 0%,#e6f4fb 55%,#e9efff 100%)}}.hero.light-theme.weather-dawn{{background:linear-gradient(118deg,#ffe8d8,#f4eafb 56%,#e4f1fb)}}.hero.light-theme.weather-dusk{{background:linear-gradient(118deg,#fbe3dc,#ebe7f8 56%,#e1f0f7)}}.hero.light-theme.weather-night{{background:linear-gradient(118deg,#e4edff,#dfe7fb 56%,#d8edf5)}}.hero.light-theme.weather-rain{{background:linear-gradient(118deg,#dceefa,#e4edf9 56%,#dbf0f0)}}.hero.light-theme.weather-cloudy{{background:linear-gradient(118deg,#eaf1f7,#e2edf4 56%,#e9edf9)}}.hero.light-theme.weather-storm{{background:linear-gradient(118deg,#e5e9f4,#dce5f0 56%,#e4edf4);animation:glow 5s ease-in-out infinite}}.hero.light-theme .moon-symbol{{color:#6076ad;text-shadow:0 0 22px rgba(80,112,175,.22)}}.hero.light-theme .cloud-shape,.hero.light-theme .cloud-shape::before,.hero.light-theme .cloud-shape::after{{filter:drop-shadow(0 3px 4px rgba(39,67,100,.16))}}
    .hero-content{{position:relative;z-index:1;flex:1;min-width:0}}.weather-scene{{display:flex;align-items:center;min-height:125px;filter:drop-shadow(0 10px 12px rgba(5,16,30,.35))}}.weather-art{{position:relative;display:block;width:164px;height:128px;flex:0 0 164px}}
    .sun-core{{position:absolute;left:35px;top:15px;width:78px;height:78px;border-radius:50%;background:radial-gradient(circle at 32% 28%,#fff6b6 0 8%,#ffd84f 35%,#ffb52f 65%,#ff8e38);box-shadow:0 0 0 9px rgba(255,195,60,.13),0 0 36px rgba(255,177,55,.35);animation:pulse 3s ease-in-out infinite}}
    .weather-art.twilight .sun-core{{left:43px;top:27px;width:68px;height:68px;clip-path:none}}.sun-horizon{{position:absolute;left:12px;right:5px;bottom:31px;height:3px;border-radius:4px;background:linear-gradient(90deg,transparent,rgba(255,250,235,.94),transparent);box-shadow:0 0 18px rgba(255,206,128,.65)}}
    .moon-symbol{{position:absolute;left:38px;top:-3px;font-size:7rem;line-height:1;color:#eaf2ff;text-shadow:0 0 25px rgba(183,208,255,.65);animation:float 4.2s ease-in-out infinite}}.weather-art.night::before{{content:"✦  ·     ·  ✧";position:absolute;inset:8px 0 auto;color:rgba(255,255,255,.85);font-size:1.1rem;letter-spacing:1rem;animation:twinkle 2.5s ease-in-out infinite alternate}}
    .cloud-shape{{position:absolute;left:22px;top:47px;width:112px;height:43px;border-radius:36px;background:linear-gradient(180deg,#fff 0%,#edf4ff 55%,#b9c9e7);box-shadow:inset 0 -5px 8px rgba(73,102,158,.16),0 8px 18px rgba(31,54,94,.14);animation:drift 4.5s ease-in-out infinite}}.cloud-shape::before,.cloud-shape::after{{content:"";position:absolute;bottom:13px;border-radius:50%;background:linear-gradient(180deg,#fff 0%,#edf4ff 56%,#c4d2eb)}}.cloud-shape::before{{left:17px;width:49px;height:49px}}.cloud-shape::after{{left:51px;bottom:16px;width:42px;height:42px}}.weather-art.partly .sun-core{{left:16px;top:12px;width:72px;height:72px}}.weather-art.partly .cloud-shape{{left:46px;top:58px;transform:scale(.82)}}.weather-art.rainy .cloud-shape,.weather-art.stormy .cloud-shape,.weather-art.snowy .cloud-shape{{left:17px;top:31px}}.rain-drops{{position:absolute;left:47px;top:81px;color:#8bd8ff;font-size:1.55rem;letter-spacing:.45rem;animation:rain .9s linear infinite}}.storm-bolt{{position:absolute;left:85px;top:75px;font-size:2.6rem;color:#ffd95e;filter:drop-shadow(0 0 10px #ffbc46);animation:flash 1.1s steps(2,end) infinite}}.snow-flakes{{position:absolute;left:45px;top:79px;color:#e9f8ff;font-size:1.4rem;letter-spacing:.55rem;animation:rain 1.6s linear infinite}}.fog-lines{{position:absolute;left:17px;top:98px;width:122px;height:3px;background:rgba(229,241,255,.78);border-radius:4px;box-shadow:12px 11px 0 rgba(229,241,255,.5),-6px 22px 0 rgba(229,241,255,.35);animation:drift 4s ease-in-out infinite alternate}}
    .hero-title{{margin:0;font-size:.95rem;letter-spacing:.13em;font-weight:750;opacity:.82}}.hero-time{{margin:6px 0 8px;font-size:.88rem;opacity:.77;font-weight:600}}.hero-cityrow{{display:flex;align-items:baseline;flex-wrap:wrap;gap:16px;margin:0 0 8px}}.hero-city{{font-size:2.35rem;font-weight:780;letter-spacing:-.04em}}.hero-temp{{font-size:1.8rem;font-weight:800}}.hero-temp small{{font-size:1rem;opacity:.8}}.hero-note{{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin:0;font-size:1rem;opacity:.9}}.condition{{padding:5px 11px;border:1px solid rgba(255,255,255,.24);border-radius:99px;background:rgba(255,255,255,.11);font-size:.84rem;font-weight:700}}
    .dog-card{{position:relative;z-index:1;width:212px;flex:0 0 212px;padding:10px 16px 15px;text-align:center;border:1px solid rgba(255,255,255,.24);border-radius:24px;background:linear-gradient(145deg,rgba(255,255,255,.2),rgba(255,255,255,.09));box-shadow:0 16px 35px rgba(5,18,34,.2);backdrop-filter:blur(12px);transition:background .3s,color .3s}}.dog-card.resting{{background:linear-gradient(145deg,rgba(150,177,205,.23),rgba(255,255,255,.08))}}.light-theme .dog-card{{color:#233953;border-color:rgba(55,94,128,.2);background:linear-gradient(145deg,rgba(255,255,255,.82),rgba(255,255,255,.55));box-shadow:0 13px 28px rgba(42,70,98,.12)}}.light-theme .dog-card.resting{{background:linear-gradient(145deg,rgba(255,255,255,.86),rgba(219,231,244,.78))}}.dog-stage{{position:relative;height:162px;display:flex;align-items:center;justify-content:center}}#dog{{width:164px;height:160px;filter:drop-shadow(0 10px 8px rgba(8,18,30,.24));animation:bob 2.6s ease-in-out infinite}}.dog-card.resting #dog{{filter:saturate(.82) drop-shadow(0 10px 8px rgba(8,18,30,.24))}}#fallback{{display:none;font-size:6rem;filter:drop-shadow(0 10px 8px rgba(8,18,30,.24));animation:bob 2.6s ease-in-out infinite}}.dog-card.resting #fallback{{animation-duration:4s}}.mood-icon{{position:absolute;right:18px;top:20px;font-size:1.3rem;filter:drop-shadow(0 2px 4px #152139)}}.puppy-mask{{position:absolute;left:50%;top:55%;width:43px;height:20px;transform:translate(-50%,-50%);border:2px solid #167f91;border-radius:4px 4px 12px 12px;background:linear-gradient(180deg,#a4f0e6,#35b4c2);box-shadow:0 3px 8px rgba(9,40,58,.32);z-index:2}}.puppy-mask::before,.puppy-mask::after{{content:"";position:absolute;top:4px;width:10px;height:9px;border-top:1.5px solid #b6f7ed}}.puppy-mask::before{{right:100%}}.puppy-mask::after{{left:100%}}.dog-label{{font-size:.91rem;font-weight:800}}.dog-note{{max-width:180px;margin:5px auto 0;font-size:.74rem;line-height:1.45;opacity:.86}}
    @keyframes sky{{from{{transform:translateX(-2%) translateY(1%)}}to{{transform:translateX(3%) translateY(-2%)}}}}@keyframes drift{{0%,100%{{transform:translateX(0) translateY(0)}}50%{{transform:translateX(9px) translateY(-4px)}}}}@keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.08)}}}}@keyframes float{{0%,100%{{transform:translateY(2px) rotate(-3deg)}}50%{{transform:translateY(-7px) rotate(3deg)}}}}@keyframes twinkle{{from{{opacity:.4}}to{{opacity:1}}}}@keyframes rain{{0%{{transform:translateY(-3px);opacity:.45}}100%{{transform:translateY(6px);opacity:1}}}}@keyframes flash{{0%,48%,100%{{opacity:.25}}49%,70%{{opacity:1}}}}@keyframes glow{{0%,90%,100%{{filter:none}}92%,96%{{filter:brightness(1.22)}}}}@keyframes bob{{0%,100%{{transform:translateY(1px)}}50%{{transform:translateY(-4px)}}}}
    @media(max-width:620px){{.hero{{min-height:300px;padding:18px;gap:8px}}.weather-scene{{min-height:95px}}.weather-art{{transform:scale(.72);transform-origin:left center;margin-right:-40px}}.hero-city{{font-size:1.6rem}}.hero-temp{{font-size:1.35rem}}.dog-card{{width:135px;flex-basis:135px;padding:7px}}.dog-stage{{height:126px}}#dog{{width:128px;height:124px}}#fallback{{font-size:4.5rem}}.dog-note{{font-size:.68rem}}.hero-note{{font-size:.85rem}}}}
    @media(prefers-reduced-motion:reduce){{*,*::before,*::after{{animation:none!important;transition:none!important}}}}
    </style></head><body>
    <div class="hero {hero_class}"><div class="hero-content"><div class="weather-scene {scene_class}">{scene}</div><p class="hero-title">WEATHER NOW</p>
    <p class="hero-time">{safe_local_clock} · {safe_timezone}</p><div class="hero-cityrow"><span class="hero-city">{safe_city}</span><span class="hero-temp">{safe_temperature}<small>{safe_temp_unit}</small></span></div>
    <p class="hero-note"><span>{safe_region}</span><span class="condition">{safe_description}</span></p></div>
    <div class="dog-card {mood_class}"><div class="dog-stage"><div id="dog"></div><div id="fallback" aria-label="Happy puppy">🐶</div>{mask_overlay}{mask_badge}</div>
    <div class="dog-label">Sky & Air Buddy · {safe_mood}</div><div class="dog-note">{safe_dog_note}</div></div></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js" onerror="document.getElementById('fallback').style.display='block'"></script>
    <script>const host=document.querySelector('.hero');function syncTheme(){{try{{const app=window.parent.document.querySelector('[data-testid="stAppViewContainer"]');if(app){{const rgb=getComputedStyle(app).backgroundColor.match(/[\d.]+/g);if(rgb&&rgb.length>=3){{const c=rgb.slice(0,3).map(Number);const lum=(.2126*c[0]+.7152*c[1]+.0722*c[2])/255;host.classList.toggle('light-theme',lum>.58);}}}}}}catch(e){{}}}}syncTheme();try{{new MutationObserver(syncTheme).observe(window.parent.document.documentElement,{{attributes:true,subtree:true,attributeFilter:['class','style','data-theme']}});}}catch(e){{}}const d={animation_data};if(window.lottie&&d){{const pup=window.lottie.loadAnimation({{container:document.getElementById('dog'),renderer:'svg',loop:true,autoplay:true,animationData:d}});pup.setSpeed('{mood_class}'==='resting'?0.72:1.08);}}else{{document.getElementById('fallback').style.display='block';}}</script>
    </body></html>"""
    components.html(html, height=340, scrolling=False)


def dog_illustration(sad: bool, masked: bool = False) -> str:
    eyes = (
        '<path d="M67 57 Q73 50 79 56 M91 56 Q97 50 103 57" fill="none" stroke="#633c2d" stroke-width="3.2" stroke-linecap="round"/>'
        if sad else
        '<g class="dog-eyes"><ellipse cx="72" cy="55" rx="4.2" ry="5.5" fill="#34231d"/><ellipse cx="96" cy="55" rx="4.2" ry="5.5" fill="#34231d"/><circle cx="73.2" cy="53.3" r="1.5" fill="#fff"/><circle cx="97.2" cy="53.3" r="1.5" fill="#fff"/></g>'
    )
    smile = ('<path d="M75 78 Q83 70 91 78" fill="none" stroke="#633c2d" stroke-width="3" stroke-linecap="round"/>' if sad else
             '<path d="M72 71 Q76 81 83 78 Q90 81 94 71" fill="none" stroke="#633c2d" stroke-width="3" stroke-linecap="round"/><path d="M80 78 Q83 77 86 78 Q87 86 83 87 Q79 86 80 78Z" fill="#f27f8a"/>')
    mood_class = "sad" if sad else "happy"
    mask = ('<g class="dog-mask"><path d="M61 69 Q84 63 107 69 L101 85 Q84 95 67 85Z" fill="url(#maskGrad)" stroke="#287f91" stroke-width="1.8"/><path d="M64 72 Q57 64 54 61 M104 72 Q111 64 114 61" fill="none" stroke="#287f91" stroke-width="2"/></g>') if masked else ""
    return (
        f'<svg class="dog-figure {mood_class}" viewBox="0 0 160 130" role="img" aria-label="Animated {mood_class} golden puppy">'
        '<defs><linearGradient id="fur" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffe7b2"/><stop offset=".42" stop-color="#f5b65e"/><stop offset=".78" stop-color="#d9823d"/><stop offset="1" stop-color="#a85432"/></linearGradient><linearGradient id="furShade" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#e6944f"/><stop offset="1" stop-color="#a85b36"/></linearGradient><linearGradient id="cream" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff9eb"/><stop offset="1" stop-color="#ead2ad"/></linearGradient><linearGradient id="maskGrad" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#8ee5df"/><stop offset="1" stop-color="#45aab8"/></linearGradient></defs>'
        '<ellipse cx="82" cy="118" rx="48" ry="7" fill="#28344b" opacity=".16"/>'
        '<g class="dog-tail"><path d="M49 92 C26 95 20 76 29 62 C37 50 54 57 49 70" fill="none" stroke="url(#furShade)" stroke-width="15" stroke-linecap="round"/><path d="M29 63 Q36 57 43 62" fill="none" stroke="#ffe2b1" stroke-width="5" stroke-linecap="round"/></g>'
        '<ellipse cx="82" cy="91" rx="42" ry="29" fill="url(#fur)"/><ellipse cx="83" cy="94" rx="22" ry="25" fill="url(#cream)"/>'
        '<path d="M55 99 Q54 113 58 116 Q66 120 70 114 L70 98 M94 98 L94 114 Q99 120 106 115 L108 98" fill="url(#furShade)" stroke="#a85b36" stroke-width="1.5"/>'
        '<ellipse cx="63" cy="115" rx="10" ry="4" fill="#ffe5c0"/><ellipse cx="101" cy="115" rx="10" ry="4" fill="#ffe5c0"/>'
        '<g class="dog-head"><g class="dog-ear-left"><path d="M56 47 Q44 11 61 21 Q76 27 75 54Z" fill="url(#furShade)"/><path d="M59 42 Q52 23 62 29 Q69 33 69 46Z" fill="#d98983" opacity=".8"/></g><g class="dog-ear-right"><path d="M95 48 Q108 11 123 22 Q130 34 108 56Z" fill="url(#furShade)"/><path d="M103 43 Q112 24 119 31 Q120 39 108 48Z" fill="#d98983" opacity=".8"/></g>'
        '<ellipse cx="83" cy="58" rx="38" ry="35" fill="url(#fur)"/><ellipse cx="68" cy="64" rx="17" ry="14" fill="url(#cream)"/><ellipse cx="98" cy="64" rx="17" ry="14" fill="url(#cream)"/>'
        '<ellipse cx="68" cy="39" rx="12" ry="5" fill="#fff" opacity=".24"/>'
        f'{eyes}<ellipse cx="83" cy="62" rx="6" ry="4.7" fill="#38231d"/><ellipse cx="81" cy="60.5" rx="1.8" ry="1.1" fill="#fff" opacity=".8"/>'
        f'<path d="M83 66 L83 70" fill="none" stroke="#704533" stroke-width="2.2" stroke-linecap="round"/>{smile}{mask}</g></svg>'
    )


def saved_place_record(place: dict) -> dict:
    return {
        "name": str(place.get("name", "")),
        "admin1": str(place.get("admin1") or ""),
        "country": str(place.get("country") or ""),
        "latitude": float(place["latitude"]),
        "longitude": float(place["longitude"]),
    }


def place_identity(place: dict) -> str:
    return f"{float(place['latitude']):.4f}|{float(place['longitude']):.4f}"


def remember_place(place: dict) -> None:
    record = saved_place_record(place)
    places = st.session_state.get("recent_places", [])
    identity = place_identity(record)
    st.session_state["recent_places"] = [
        record,
        *[item for item in places if place_identity(item) != identity],
    ][:6]


st.title("🌍 Global Air & Weather Explorer")
st.caption("Explore weather estimates and reported air-quality monitor readings for cities around the world.")

with st.sidebar:
    st.markdown('<div class="search-heading">Find a place <span class="search-weather-icon" aria-hidden="true"><i class="side-sun"></i><i class="side-cloud"></i></span></div>', unsafe_allow_html=True)
    city_selection = CITY_AUTOCOMPLETE(
        value=st.session_state.get("city_query", "New Delhi"),
        label="Search any city worldwide",
        placeholder="Try Delhi, London, or Tokyo",
        key="city-autocomplete",
        default=None,
    )
    if isinstance(city_selection, dict):
        if city_selection.get("type") == "clear":
            st.session_state["city_query"] = ""
        elif city_selection.get("type") == "select":
            chosen_place = city_selection.get("place") or {}
            selection_id = "|".join(str(chosen_place.get(part, "")) for part in ("name", "admin1", "latitude", "longitude"))
            if chosen_place.get("name") and selection_id != st.session_state.get("last-city-selection"):
                st.session_state["place"] = chosen_place
                st.session_state["city_query"] = city_selection.get("label") or chosen_place["name"]
                st.session_state["last-city-selection"] = selection_id
                remember_place(chosen_place)
                st.rerun()
    unit_choice = st.selectbox("Temperature units", ["Celsius (°C)", "Fahrenheit (°F)"], key="temperature-units")
    temperature_unit = "fahrenheit" if unit_choice.startswith("Fahrenheit") else "celsius"
    st.divider()
    st.caption("Weather and air-quality forecast are model estimates. Sensor readings appear separately when available.")
    st.caption("Pollen estimates from this service are currently limited to Europe.")

if "place" not in st.session_state:
    try:
        defaults = search_city("New Delhi", country_code="IN")
        if defaults:
            st.session_state["place"] = defaults[0]
            st.session_state["city_matches"] = defaults
        else:
            st.error("Could not load the default city. Check your internet connection and refresh.")
            st.stop()
    except requests.RequestException as exc:
        st.error(f"Could not connect to the location service: {exc}")
        st.stop()

if not st.session_state.get("recent_places"):
    remember_place(st.session_state["place"])
current_place_record = saved_place_record(st.session_state["place"])
favorite_places = st.session_state.setdefault("favorite_places", [])
current_identity = place_identity(current_place_record)
with st.sidebar:
    st.divider()
    st.markdown("#### Quick places")
    if any(place_identity(item) == current_identity for item in favorite_places):
        if st.button("★ Saved place · click to remove", key="remove-current-favorite"):
            st.session_state["favorite_places"] = [
                item for item in st.session_state["favorite_places"]
                if place_identity(item) != current_identity
            ]
            st.rerun()
    elif st.button("☆ Save this city", key="save-current-favorite"):
        st.session_state["favorite_places"] = [current_place_record, *favorite_places][:8]
        st.rerun()

    for group_name, place_list in (
        ("Saved", st.session_state.get("favorite_places", [])),
        ("Recent", st.session_state.get("recent_places", [])),
    ):
        if place_list:
            st.caption(group_name)
            for index, quick_place in enumerate(place_list):
                quick_label = f"📍 {quick_place['name']}, {quick_place.get('admin1') or quick_place.get('country') or 'Location'}"
                quick_key = f"quick-{group_name.lower()}-{index}-{place_identity(quick_place)}"
                if st.button(quick_label, key=quick_key):
                    st.session_state["place"] = quick_place
                    st.session_state["city_query"] = quick_label[2:]
                    remember_place(quick_place)
                    st.rerun()
    st.caption("Saved and recent places stay available while this app session is open.")

place = st.session_state["place"]
city = place["name"]
region = place.get("admin1") or place.get("country") or "Location"
latitude, longitude = float(place["latitude"]), float(place["longitude"])

try:
    weather = get_weather(latitude, longitude, temperature_unit)
    air = get_air_forecast(latitude, longitude)
except requests.RequestException as exc:
    st.error(f"Could not load weather or air-quality data: {exc}")
    st.info("Please refresh in a moment. The data services may be temporarily unavailable.")
    st.stop()

current_weather = weather.get("current", {})
current_air = air.get("current", {})
weather_units = weather.get("current_units", {})
air_units = air.get("current_units", {})

weather_code_value = current_weather.get("weather_code")
weather_code = int(weather_code_value) if weather_code_value is not None else -1
temp_now = current_weather.get("temperature_2m")
temp_celsius = ((float(temp_now) - 32) * 5 / 9 if temperature_unit == "fahrenheit" else float(temp_now)) if temp_now is not None else None
aqi_now = current_air.get("us_aqi")
stormy = weather_code in (95, 96, 99)
rainy = weather_code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82)
too_hot = temp_celsius is not None and temp_celsius >= 35
mask_on = aqi_now is not None and float(aqi_now) > 150
very_poor_air = aqi_now is not None and float(aqi_now) > 250
uv_now = current_weather.get("uv_index")
high_uv = uv_now is not None and float(uv_now) >= 8
dog_sad = stormy or too_hot or high_uv or very_poor_air
if mask_on:
    mood, dog_note = "mask on · resting indoors", "Air quality is elevated in this model estimate, so the pup is taking it easy indoors."
elif stormy:
    mood, dog_note = "taking cover", "The storm animation is active; our pup is sheltering inside."
elif too_hot or high_uv:
    mood, dog_note = "taking a cool break", "It is warm or the UV estimate is high, so the pup is resting in the shade."
elif rainy:
    mood, dog_note = "happy in the rain", "Our pup enjoys the rain from a cozy, dry spot."
else:
    mood, dog_note = "happy", "Our pup is enjoying this weather snapshot."
dog_svg = dog_illustration(dog_sad, masked=mask_on)
display_weather_card(city, region, weather, dog_svg, mood, dog_note)

daily = weather.get("daily", {})
if daily.get("time"):
    st.subheader("The week ahead")
    st.markdown(f'<p class="section-intro">A quick look at daily conditions and rain chances. Temperatures in {weather_units.get("temperature_2m", "°C")}.</p>', unsafe_allow_html=True)
    forecast_count = min(7, len(daily.get("time", [])))
    day_cols = st.columns(forecast_count, gap="small")
    for index in range(forecast_count):
        day_date = pd.to_datetime(daily["time"][index])
        day_label = "Today" if index == 0 else day_date.strftime("%a")
        condition, icon = weather_description(daily.get("weather_code", [None] * forecast_count)[index])
        high = daily.get("temperature_2m_max", [None] * forecast_count)[index]
        low = daily.get("temperature_2m_min", [None] * forecast_count)[index]
        rain_chance = daily.get("precipitation_probability_max", [None] * forecast_count)[index]
        with day_cols[index]:
            st.markdown(display_day_card(day_label, condition, icon, high, low, rain_chance, weather_units.get("temperature_2m", "°C")), unsafe_allow_html=True)

st.subheader("Current conditions")
st.markdown('<p class="section-intro">Live model estimates for the selected city.</p>', unsafe_allow_html=True)
metric_cols = st.columns(5)
metric_cols[0].metric("Temperature", f"{current_weather.get('temperature_2m', '—')} {weather_units.get('temperature_2m', '°C')}")
metric_cols[1].metric("Feels like", f"{current_weather.get('apparent_temperature', '—')} {weather_units.get('apparent_temperature', '°C')}")
metric_cols[2].metric("Humidity", f"{current_weather.get('relative_humidity_2m', '—')} {weather_units.get('relative_humidity_2m', '%')}")
metric_cols[3].metric(f"PM2.5 estimate ({air_units.get('pm2_5', 'µg/m³')})", f"{current_air.get('pm2_5', '—')}")
metric_cols[4].metric("Modelled US AQI", f"{current_air.get('us_aqi', '—')}")
aqi_value = current_air.get("us_aqi")
if aqi_value is None or pd.isna(aqi_value):
    badge_color, badge_bg = "#667085", "rgba(120,130,145,.16)"
else:
    badge_color, badge_bg = ("#16834f", "rgba(35,170,105,.16)") if float(aqi_value) <= 50 else ("#9a7200", "rgba(235,190,35,.2)") if float(aqi_value) <= 100 else ("#b96616", "rgba(243,146,40,.18)") if float(aqi_value) <= 150 else ("#b43b4b", "rgba(225,72,95,.17)")
metric_cols[4].markdown(
    f'<span class="aqi-pill" style="color:{badge_color};background:{badge_bg}">{aqi_label(aqi_value)}</span>',
    unsafe_allow_html=True,
)

daily_times = daily.get("time", [])
today_rain = daily.get("precipitation_sum", [None])[0] if daily_times else None
today_rain_chance = daily.get("precipitation_probability_max", [None])[0] if daily_times else None
sunrise = daily.get("sunrise", [None])[0] if daily_times else None
sunset = daily.get("sunset", [None])[0] if daily_times else None
def format_local_time(value):
    timestamp = pd.to_datetime(value, errors="coerce")
    return timestamp.strftime("%I:%M %p").lstrip("0") if pd.notna(timestamp) else "—"

st.subheader("Weather details")
st.markdown('<p class="weather-details-intro">Wind direction is for the selected city. Forecast values are model estimates.</p>', unsafe_allow_html=True)
wind_speed = current_weather.get("wind_speed_10m")
wind_speed_unit = weather_units.get("wind_speed_10m", "km/h")
wind_direction = current_weather.get("wind_direction_10m")
gust_speed = current_weather.get("wind_gusts_10m")
gust_unit = weather_units.get("wind_gusts_10m", wind_speed_unit)
humidity_value = current_weather.get("relative_humidity_2m")
first_detail_row = st.columns([1.6, 1, 1], gap="medium")
with first_detail_row[0]:
    st.markdown(wind_compass_card(wind_direction, wind_speed, wind_speed_unit), unsafe_allow_html=True)
with first_detail_row[1]:
    st.markdown(gust_detail_card(gust_speed, gust_unit), unsafe_allow_html=True)
with first_detail_row[2]:
    humidity_text = f"{humidity_value} {weather_units.get('relative_humidity_2m', '%')}" if humidity_value is not None else "—"
    st.markdown(display_detail_card("Relative humidity", humidity_text), unsafe_allow_html=True)

visibility_raw = current_weather.get("visibility")
visibility_unit = weather_units.get("visibility", "m")
if visibility_raw is not None and not pd.isna(visibility_raw) and visibility_unit.lower() in {"m", "metre", "meter", "meters"}:
    visibility_value, visibility_display_unit = float(visibility_raw) / 1000, "km"
elif visibility_raw is not None and not pd.isna(visibility_raw):
    visibility_value, visibility_display_unit = float(visibility_raw), visibility_unit
else:
    visibility_value, visibility_display_unit = None, "km"
cloud_cover = current_weather.get("cloud_cover")
precipitation_now = current_weather.get("precipitation")
pressure = current_weather.get("pressure_msl")
pressure_unit = weather_units.get("pressure_msl", "hPa")
second_detail_row = st.columns(4, gap="medium")
with second_detail_row[0]:
    st.markdown(progress_detail_card("Cloud cover", cloud_cover, "%", cloud_cover if cloud_cover is not None and not pd.isna(cloud_cover) else 0, "Estimated cloud coverage"), unsafe_allow_html=True)
with second_detail_row[1]:
    visibility_text = f"{visibility_value:.1f}" if visibility_value is not None else "—"
    st.markdown(display_detail_card("Visibility", f"{visibility_text} {visibility_display_unit}"), unsafe_allow_html=True)
with second_detail_row[2]:
    rain_current_text = f"{float(precipitation_now):.1f} mm" if precipitation_now is not None and not pd.isna(precipitation_now) else "—"
    rain_today_text = f"Today: {today_rain} mm · {today_rain_chance}% chance" if today_rain is not None else "Daily estimate unavailable"
    st.markdown(display_detail_card("Precipitation · current", rain_current_text, rain_today_text), unsafe_allow_html=True)
with second_detail_row[3]:
    pressure_text = f"{float(pressure):.0f}" if pressure is not None and not pd.isna(pressure) else "—"
    st.markdown(display_detail_card("Sea-level pressure", f"{pressure_text} {pressure_unit}", '<span class="pressure-dial" aria-hidden="true">↗</span> Model pressure estimate'), unsafe_allow_html=True)

third_detail_row = st.columns([1, 1, 1], gap="medium")
with third_detail_row[0]:
    st.markdown(uv_detail_card(current_weather.get("uv_index")), unsafe_allow_html=True)
with third_detail_row[1]:
    st.markdown(display_detail_card("Sunrise · local", format_local_time(sunrise)), unsafe_allow_html=True)
with third_detail_row[2]:
    st.markdown(display_detail_card("Sunset · local", format_local_time(sunset)), unsafe_allow_html=True)

tab_weather, tab_air, tab_stations, tab_assistant = st.tabs(
    ["7-day weather", "Air-quality outlook", "Nearby sensors", "Ask for a quick brief"]
)

with tab_weather:
    hourly = weather.get("hourly", {})
    if hourly.get("time"):
        st.markdown("#### Coming up")
        hourly_frame = pd.DataFrame({
            "time": pd.to_datetime(hourly.get("time", []), errors="coerce"),
            "temperature": hourly.get("temperature_2m", []),
            "rain": hourly.get("precipitation_probability", []),
            "code": hourly.get("weather_code", []),
        }).dropna(subset=["time"])
        current_time = pd.to_datetime(current_weather.get("time"), errors="coerce")
        if pd.notna(current_time):
            upcoming = hourly_frame.loc[hourly_frame["time"] >= current_time].head(8)
            if upcoming.empty:
                upcoming = hourly_frame.head(8)
        else:
            upcoming = hourly_frame.head(8)
        if not upcoming.empty:
            hour_cols = st.columns(len(upcoming), gap="small")
            for position, (_, row) in enumerate(upcoming.iterrows()):
                condition, icon = weather_description(row["code"], row["time"])
                time_label = "Now" if position == 0 else row["time"].strftime("%I %p").lstrip("0")
                with hour_cols[position]:
                    st.markdown(display_hour_card(time_label, condition, icon, row["temperature"], row["rain"], weather_units.get("temperature_2m", "°C")), unsafe_allow_html=True)
    daily = weather.get("daily", {})
    if daily.get("time"):
        temp_symbol = weather_units.get("temperature_2m", "°C")
        low_label, high_label = f"Low {temp_symbol}", f"High {temp_symbol}"
        forecast = pd.DataFrame({
            "date": pd.to_datetime(daily["time"]),
            low_label: daily.get("temperature_2m_min", []),
            high_label: daily.get("temperature_2m_max", []),
            "Rain chance %": daily.get("precipitation_probability_max", []),
            "Rain mm": daily.get("precipitation_sum", []),
            "Code": daily.get("weather_code", []),
        })
        forecast["Condition"] = forecast["Code"].map(lambda code: weather_description(code)[0])
        st.plotly_chart(
            px.line(forecast, x="date", y=[low_label, high_label], markers=True,
                    title="Seven-day temperature outlook"),
            width="stretch",
        )
        st.dataframe(forecast.drop(columns="Code"), hide_index=True, width="stretch")
    st.caption("Forecasts are computer-model guidance and can change. Weather data by Open-Meteo.")

with tab_air:
    hourly = air.get("hourly", {})
    if hourly.get("time"):
        air_frame = pd.DataFrame({"time": pd.to_datetime(hourly["time"])})
        for field, label in [("pm2_5", "PM2.5 (µg/m³)"), ("pm10", "PM10 (µg/m³)"), ("us_aqi", "US AQI")]:
            if field in hourly:
                air_frame[label] = hourly[field]
        plot_fields = [field for field in ["PM2.5 (µg/m³)", "PM10 (µg/m³)"] if field in air_frame]
        if plot_fields:
            st.plotly_chart(
                px.line(air_frame, x="time", y=plot_fields, title="Five-day modelled pollutant outlook"), width="stretch",
            )
        st.dataframe(air_frame, hide_index=True, width="stretch")
    st.info("This city-scale air-quality forecast is modelled, not a measurement from a nearby sensor. Open-Meteo uses global atmospheric composition forecasts; local monitor readings can differ.")
    st.caption("Pollen fields from this data service are limited to Europe and may not be available for every place there.")

with tab_stations:
    st.write("Explore reported readings from OpenAQ monitoring locations near the selected city. These sensor observations are separate from the modelled city forecast.")
    api_key = os.getenv("OPENAQ_API_KEY")
    if not api_key:
        st.info("To show monitoring locations worldwide, add your OpenAQ API key to the local .env file. Never paste the key into chat or GitHub.")
    else:
        try:
            radius_km = st.select_slider("Search distance from this city", options=[10, 25, 50, 100], value=25, format_func=lambda value: f"{value} km")
            stations = nearby_openaq_stations(latitude, longitude, radius_km, api_key)
            if not stations:
                st.info(f"OpenAQ returned no monitoring locations within {radius_km} km. Try a larger search distance or another city. Coverage depends on what providers publish.")
            else:
                map_rows = []
                for item in stations:
                    coords = item.get("coordinates") or {}
                    lat, lon = coords.get("latitude"), coords.get("longitude")
                    if lat is not None and lon is not None:
                        map_rows.append({"latitude": lat, "longitude": lon})
                if map_rows:
                    st.markdown("#### Monitoring locations near this city")
                    st.map(pd.DataFrame(map_rows), latitude="latitude", longitude="longitude", zoom=8)
                    st.caption("Each marker is an OpenAQ monitoring location. A location may contain multiple pollutant sensors; markers do not guarantee a recent reading.")
                station_labels = []
                for item in stations:
                    distance = item.get("distance_km")
                    distance_label = f"{distance:.1f} km" if isinstance(distance, (int, float)) else "distance unknown"
                    provider = (item.get("provider") or {}).get("name", "source unknown")
                    station_labels.append(f"{item.get('name', 'Unnamed station')} · {distance_label} · {provider}")
                selected_idx = st.selectbox("Choose a nearby monitoring location", range(len(stations)),
                                            format_func=lambda idx: station_labels[idx])
                station = stations[selected_idx]
                latest = get_latest_station_readings(int(station["id"]), api_key)
                sensors_by_id = {int(sensor["id"]): sensor for sensor in station.get("sensors", []) if sensor.get("id") is not None}
                reading_rows = []
                for reading in latest:
                    sensor_id = reading.get("sensorsId")
                    if sensor_id is None:
                        continue
                    sensor = sensors_by_id.get(int(sensor_id))
                    if not sensor:
                        continue
                    parameter = sensor.get("parameter") or {}
                    timestamp = reading.get("datetime") or {}
                    reading_rows.append({
                        "Pollutant / measure": parameter.get("displayName") or parameter.get("name") or sensor.get("name", "Measure"),
                        "Latest reported value": reading.get("value", "—"),
                        "Unit": parameter.get("units", ""),
                        "Reported at (local)": timestamp.get("local") or timestamp.get("utc") or "Time not supplied",
                    })
                if reading_rows:
                    st.markdown(f"#### Latest readings · {station.get('name', 'Selected location')}")
                    st.dataframe(pd.DataFrame(reading_rows), hide_index=True, width="stretch")
                else:
                    st.info("This location is listed, but OpenAQ did not return a latest reading for its sensors.")
                with st.expander("Station source and license details"):
                    st.write(f"Provider: {(station.get('provider') or {}).get('name', 'Not supplied')}")
                    st.write(f"Owner: {(station.get('owner') or {}).get('name', 'Not supplied')}")
                    licenses = station.get("licenses") or []
                    st.write("Licenses: " + (", ".join(item.get("name", "Unnamed") for item in licenses) if licenses else "Check OpenAQ location details"))
                    st.caption("OpenAQ coverage, provider updates, and licensing vary by station. Verify source terms before redistributing readings.")
        except requests.RequestException as exc:
            st.warning(f"Could not load nearby station details: {exc}")

with tab_assistant:
    st.markdown("### Ask the city brief")
    st.write(f"Try: *What is the temperature and air quality in {city} right now?*")
    with st.form("brief-form"):
        question = st.text_input("Type a question about the selected city")
        ask = st.form_submit_button("Get answer", type="primary")
    if ask:
        if question.strip():
            st.info(smart_brief(question, city, weather, air))
        else:
            st.warning("Type a question first.")
    st.caption("This first assistant gives a data-grounded summary from the current forecast. It does not call an external generative-AI service. Voice input can be added as a separate browser feature later.")

st.divider()
st.caption("Data credits: Open-Meteo weather and air-quality model data; Open-Meteo Geocoding location search (location names based on GeoNames); OpenAQ station observations when available. Forecast values are estimates, not official alerts. Weather values are gridded predictions, not measurements at the selected address.")

with st.expander("Previous New Delhi sample analysis"):
    if not DATA.exists():
        st.info("The previous sample file was not found. Run python src/download_data.py from the project folder to recreate it.")
    else:
        data = pd.read_csv(DATA, parse_dates=["date"])
        if data.empty:
            st.warning("The saved sample dataset is empty.")
        else:
            st.write(f"Sample: {len(data)} daily PM2.5 readings from {data['date'].min():%Y-%m-%d} to {data['date'].max():%Y-%m-%d}.")
            st.plotly_chart(px.line(data, x="date", y="pm25", title="New Delhi sample: daily PM2.5"), width="stretch")
            fields = [column for column in ["pm25", "temperature_2m", "relative_humidity_2m", "precipitation"] if column in data]
            numeric = data[fields].apply(pd.to_numeric, errors="coerce")
            valid = numeric.notna().any(axis=1)
            model_input = numeric.loc[valid].fillna(numeric.loc[valid].median()).dropna(axis=1, how="all")
            if model_input.shape[0] >= 30 and model_input.shape[1] > 0:
                labels = IsolationForest(contamination=0.05, random_state=42).fit_predict(model_input)
                reviewed = data.loc[valid].copy()
                reviewed["model_flag"] = ["Review" if label == -1 else "Typical" for label in labels]
                unusual = reviewed.loc[reviewed["model_flag"] == "Review"].sort_values("date", ascending=False)
                st.write(f"Isolation Forest flagged **{len(unusual)} of {len(reviewed)}** days for review. These are statistical prompts, not verified events.")
                st.dataframe(unusual, hide_index=True, width="stretch")
            st.caption("OpenAQ station sample and Open-Meteo historical weather. Missing air-quality dates are gaps, not zero readings.")
