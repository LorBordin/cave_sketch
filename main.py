from cave_sketch.survey.survey import draw_survey
from cave_sketch.parse_dxf import parse_dxf
import argparse

def main(map_dxf_file, section_dxf_path):

    map_df = parse_dxf(
        map_dxf_file, 
        out_file_path="./data/map.csv"
    )
    section_df = parse_dxf(
        section_dxf_path, 
        out_file_path="./data/section.csv"
    )

    draw_survey(
        title="Test",
        csv_map_path="./data/map.csv",
        csv_section_path="./data/section.csv",
        output_path="./test.pdf"
    )

if __name__ == "__main__":

    #ap = argparse.ArgumentParser()
    #ap.add_argument("-m", "--map-path", required=True)
    #ap.add_argument("-s", "--section-path", required=True)
    #args = ap.parse_args()
    

    main(
        map_dxf_file="../cave_survey/grotta_zocchi/grotta_zocchi-1p.dxf", #args.map_path,
        section_dxf_path="../cave_survey/grotta_zocchi/grotta_zocchi-1s.dxf" #args.section_path
    )