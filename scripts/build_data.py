import json
import os
import glob
import shutil

DATA_SOURCE_DIR = 'data_source'
OUTPUT_DIR = 'docs/data'

def main():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    municipalities_list = []

    # Process each JSON file in data_source
    json_files = glob.glob(os.path.join(DATA_SOURCE_DIR, '*.json'))

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        municipality_info = data.get('municipality', {})
        if not municipality_info:
            print(f"Skipping {json_file}: No municipality info found.")
            continue

        m_id = municipality_info.get('id')
        if not m_id:
            print(f"Skipping {json_file}: No municipality ID found.")
            continue

        # Add to list
        municipalities_list.append(municipality_info)

        # Create municipality output directory
        m_output_dir = os.path.join(OUTPUT_DIR, m_id)
        if not os.path.exists(m_output_dir):
            os.makedirs(m_output_dir)

        # Write all.json
        with open(os.path.join(m_output_dir, 'all.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Write category files
        categories = data.get('categories', [])
        for category in categories:
            c_id = category.get('id')
            if not c_id:
                continue

            # Construct category specific data
            category_data = {
                "municipality": municipality_info,
                "category": category
            }

            with open(os.path.join(m_output_dir, f'{c_id}.json'), 'w', encoding='utf-8') as f:
                json.dump(category_data, f, ensure_ascii=False, indent=2)

    # Write municipalities list
    with open(os.path.join(OUTPUT_DIR, 'municipalities.json'), 'w', encoding='utf-8') as f:
        json.dump(municipalities_list, f, ensure_ascii=False, indent=2)

    print("Build complete.")

if __name__ == "__main__":
    main()
