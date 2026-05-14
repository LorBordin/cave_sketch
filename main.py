from cave_sketch.parse_dxf import parse_dxf
from cave_sketch.survey.survey import draw_survey


def main(map_dxf_file, section_dxf_path):
    parse_dxf(map_dxf_file, out_file_path="./data/map.csv")
    parse_dxf(section_dxf_path, out_file_path="./data/section.csv")

    draw_survey(
        title="Test",
        csv_map_path="./data/map.csv",
        csv_section_path="./data/section.csv",
        output_path="./test.pdf",
        rule_length=100,
    )


if __name__ == "__main__":
    # Example paths (placeholders)
    MAP_PATH = "data/sample.dxf"
    SECTION_PATH = "data/sample.dxf"

    main(map_dxf_file=MAP_PATH, section_dxf_path=SECTION_PATH)
