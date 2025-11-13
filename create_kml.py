from typing import List
import json

from cave_sketch.backend_renders import render_to_kml

def main(json_paths: List[str], output_path: str):

    data = []
    for path in json_paths:
        with open (path, 'r') as f:
            data.append(json.load(f))
    
    kml_str = render_to_kml(data, layer_name="My Map Features")

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(kml_str)

if __name__ == "__main__":

    INPUT_JSONS = [
        "/Users/bordil/projects/cave_survey/sistema_vallelunga_24/sistema_24.json",
        "/Users/bordil/projects/cave_survey/sistema_vallelunga_24/val_05_24_bis.json",
        "/Users/bordil/projects/cave_survey/sistema_vallelunga_24/val_07_24_bis.json",
    ]
    OUTPOUT_KML = "./sistema_24.kml"

    main(INPUT_JSONS, OUTPOUT_KML)