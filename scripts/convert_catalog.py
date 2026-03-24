#!/usr/bin/env python3
"""
service_catalog.json → data_source/{municipality-id}.json 変換スクリプト

フラットな行政サービスデータを、カテゴリ別階層構造に変換する。
"""

import json
import os
import re
import argparse
from collections import defaultdict

CATEGORY_ID_MAP = {
    "子育て・教育": "childcare-education",
    "健康・医療": "health-medical",
    "福祉・介護": "welfare-nursing",
    "補助金・助成金": "subsidies-grants",
    "防災・災害対応": "disaster-prevention",
    "環境・ごみ・リサイクル": "environment-recycling",
    "住まい・住宅支援": "housing-support",
    "市民生活・手続き": "civic-life-procedures",
    "産業・事業者支援": "industry-business",
    "文化・スポーツ": "culture-sports",
    "交通・移動支援": "transportation",
    "水道・上下水道": "water-sewage",
    "公園・緑地・レクリエーション": "parks-recreation",
    "男女共同参画・人権・相談": "gender-equality-rights",
    "消費生活・トラブル対応": "consumer-affairs",
    "まちづくり・都市整備": "urban-planning",
    "行政運営・計画・評価": "administration-planning",
    "デジタル・IT関連": "digital-it",
    "ペット・動物愛護": "pets-animals",
    "意見・要望・苦情受付": "feedback-requests",
    "その他": "others",
}

# 和暦→西暦マッピング
ERA_MAP = {
    "令和": 2018,
    "平成": 1988,
    "昭和": 1925,
}


def convert_wareki_to_iso(date_str):
    """和暦日付をISO形式(YYYY-MM-DD)に変換する。既にISO形式ならそのまま返す。"""
    if not date_str:
        return ""

    # 既にISO形式の場合
    iso_match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if iso_match:
        return date_str

    # 和暦パターン: 令和7年5月28日, 令和元年1月1日
    wareki_match = re.match(r'(令和|平成|昭和)(元|\d+)年(\d+)月(\d+)日', date_str)
    if wareki_match:
        era = wareki_match.group(1)
        year_str = wareki_match.group(2)
        month = int(wareki_match.group(3))
        day = int(wareki_match.group(4))

        if year_str == "元":
            year_num = 1
        else:
            year_num = int(year_str)

        base = ERA_MAP.get(era, 2018)
        western_year = base + year_num

        return f"{western_year:04d}-{month:02d}-{day:02d}"

    return date_str


def extract_service_id(url, used_ids):
    """URLの末尾数字からサービスIDを生成する。重複時はサフィックスを付与。"""
    if url:
        # URLパス末尾の数字を抽出
        match = re.search(r'/(\d+)(?:[/.]|$)', url)
        if match:
            base_id = f"svc-{match.group(1)}"
            final_id = base_id
            counter = 2
            while final_id in used_ids:
                final_id = f"{base_id}-{counter}"
                counter += 1
            used_ids.add(final_id)
            return final_id

    # フォールバック: 連番
    counter = 1
    while True:
        fallback_id = f"svc-{counter:04d}"
        if fallback_id not in used_ids:
            used_ids.add(fallback_id)
            return fallback_id
        counter += 1


def convert_catalog(input_path, municipality_id, municipality_name, homepage, output_dir):
    """service_catalog.json を data_source 形式に変換する。"""
    with open(input_path, 'r', encoding='utf-8') as f:
        services_raw = json.load(f)

    # カテゴリごとにグルーピング
    categories_map = defaultdict(list)
    all_dates = []
    used_ids = set()

    for svc in services_raw:
        # プライマリカテゴリ = サービスラベルの最初の要素
        service_labels = svc.get("サービスラベル", [])
        primary_category = service_labels[0] if service_labels else "その他"

        # URL取得
        url_obj = svc.get("URL", {})
        url = url_obj.get("items", "") if isinstance(url_obj, dict) else ""

        # サービスID生成
        service_id = extract_service_id(url, used_ids)

        # 日付変換
        published_date = convert_wareki_to_iso(svc.get("公開日", ""))
        if published_date:
            all_dates.append(published_date)

        service_obj = {
            "id": service_id,
            "name": svc.get("タイトル", ""),
            "url": url,
            "description": svc.get("サービス内容", ""),
            "tags": svc.get("対象者ラベル", []),
            "serviceLabels": service_labels,
            "eligibility": svc.get("対象者", ""),
            "howToApply": svc.get("条件・申し込み方法", ""),
            "publishedDate": published_date,
        }

        categories_map[primary_category].append(service_obj)

    # カテゴリをサービス件数の降順でソート
    sorted_categories = sorted(categories_map.items(), key=lambda x: len(x[1]), reverse=True)

    categories_list = []
    for cat_name, cat_services in sorted_categories:
        cat_id = CATEGORY_ID_MAP.get(cat_name, "others")
        categories_list.append({
            "id": cat_id,
            "name": cat_name,
            "services": cat_services,
        })

    # last_updated: 全サービスの公開日のうち最新
    last_updated = max(all_dates) if all_dates else ""

    output_data = {
        "municipality": {
            "id": municipality_id,
            "name": municipality_name,
            "homepage": homepage,
            "last_updated": last_updated,
        },
        "categories": categories_list,
    }

    # 出力
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{municipality_id}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    total_services = sum(len(cat["services"]) for cat in categories_list)
    print(f"変換完了: {total_services}件 → {len(categories_list)}カテゴリ")
    print(f"出力: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="service_catalog.json を data_source 形式に変換する")
    parser.add_argument("input", help="入力ファイルパス (service_catalog.json)")
    parser.add_argument("--municipality-id", default="kokubunji-city", help="自治体ID (デフォルト: kokubunji-city)")
    parser.add_argument("--municipality-name", default="国分寺市", help="自治体名 (デフォルト: 国分寺市)")
    parser.add_argument("--homepage", default="https://www.city.kokubunji.tokyo.jp", help="公式HP URL")
    parser.add_argument("--output-dir", default="data_source", help="出力先ディレクトリ (デフォルト: data_source)")

    args = parser.parse_args()

    convert_catalog(args.input, args.municipality_id, args.municipality_name, args.homepage, args.output_dir)


if __name__ == "__main__":
    main()
