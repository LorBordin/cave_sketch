from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure


def export_pdf(fig: Figure, output_path: Path) -> Path:
    """
    Export a matplotlib figure to a PDF file.
    
    Args:
        fig: The matplotlib Figure to export.
        output_path: The filesystem path where the PDF will be saved.
        
    Returns:
        The output path.
    """
    with PdfPages(output_path) as pdf:
        pdf.savefig(fig)
    return output_path
