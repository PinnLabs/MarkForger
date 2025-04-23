import os
import uuid
import shutil
import markdown
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import zipfile

from app.core.config import settings


class ConversionService:
    def __init__(self):
        os.makedirs(settings.STORAGE_PATH, exist_ok=True)
        
    def _create_conversion_dir(self, user_id: Optional[str] = None) -> str:
        """Create a unique directory for the conversion"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        if user_id:
            dir_name = f"{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}"
        else:
            dir_name = f"anonymous_{timestamp}_{uuid.uuid4().hex[:8]}"
            
        conversion_dir = os.path.join(settings.STORAGE_PATH, dir_name)
        os.makedirs(conversion_dir, exist_ok=True)
        return conversion_dir
    
    def _create_base_css(self, output_dir: str) -> str:
        """Create base CSS file for the site"""
        css_dir = os.path.join(output_dir, "css")
        os.makedirs(css_dir, exist_ok=True)
        
        css_file = os.path.join(css_dir, "style.css")
        with open(css_file, "w") as f:
            f.write("""
/* Base styles for MD to HTML conversion */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
}

h1 { font-size: 2em; }
h2 { font-size: 1.75em; }
h3 { font-size: 1.5em; }
h4 { font-size: 1.25em; }
h5 { font-size: 1em; }
h6 { font-size: 0.85em; }

p {
    margin: 1em 0;
}

a {
    color: #0366d6;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

code {
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
    background-color: #f6f8fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 85%;
}

pre {
    background-color: #f6f8fa;
    border-radius: 3px;
    padding: 16px;
    overflow: auto;
}

pre code {
    background-color: transparent;
    padding: 0;
}

blockquote {
    padding: 0 1em;
    color: #6a737d;
    border-left: 0.25em solid #dfe2e5;
    margin: 1em 0;
}

ul, ol {
    padding-left: 2em;
    margin: 1em 0;
}

img {
    max-width: 100%;
    height: auto;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}

table th, table td {
    border: 1px solid #dfe2e5;
    padding: 6px 13px;
}

table th {
    background-color: #f6f8fa;
    font-weight: 600;
}

hr {
    height: 0.25em;
    padding: 0;
    margin: 24px 0;
    background-color: #e1e4e8;
    border: 0;
}
            """)
        return css_file
    
    def convert_markdown_to_html(self, 
                                content: Dict[str, str], 
                                user_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Converts markdown content to HTML files
        
        Args:
            content: Dictionary with file names as keys and markdown content as values
            user_id: Optional user ID for authenticated users
            
        Returns:
            Tuple with (conversion_id, conversion_path)
        """
        conversion_dir = self._create_conversion_dir(user_id)
        conversion_id = os.path.basename(conversion_dir)
        
        # Create CSS
        self._create_base_css(conversion_dir)
        
        # Process each markdown file
        for filename, md_content in content.items():
            # Ensure filename has .md extension
            if not filename.endswith('.md'):
                filename = f"{filename}.md"
                
            # Save original markdown
            md_file_path = os.path.join(conversion_dir, filename)
            with open(md_file_path, "w") as f:
                f.write(md_content)
                
            # Convert to HTML
            html_content = markdown.markdown(
                md_content,
                extensions=[
                    'markdown.extensions.extra',
                    'markdown.extensions.codehilite', 
                    'markdown.extensions.tables',
                    'markdown.extensions.toc'
                ]
            )
            
            # Create HTML with template
            html_filename = filename.replace('.md', '.html')
            html_file_path = os.path.join(conversion_dir, html_filename)
            
            with open(html_file_path, "w") as f:
                f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_filename}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    {html_content}
</body>
</html>""")
        
        return conversion_id, conversion_dir
    
    def create_zip(self, conversion_id: str) -> str:
        """Create a zip file of the converted site"""
        conversion_path = os.path.join(settings.STORAGE_PATH, conversion_id)
        if not os.path.exists(conversion_path):
            raise FileNotFoundError(f"Conversion {conversion_id} not found")
            
        zip_path = f"{conversion_path}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(conversion_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, conversion_path)
                    zipf.write(file_path, arcname)
                    
        return zip_path
    
    def get_preview_url(self, conversion_id: str) -> str:
        # Get URL for previewing the converted site
        # In a real implementation, this would point to where the site is hosted
        return f"/preview/{conversion_id}"
        
    def cleanup_old_conversions(self, days_to_keep: int = 7) -> List[str]:
        # Clean up conversions older than the specified number of days
        removed_dirs = []
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for item in os.listdir(settings.STORAGE_PATH):
            item_path = os.path.join(settings.STORAGE_PATH, item)
            if os.path.isdir(item_path):
                mod_time = os.path.getmtime(item_path)
                if mod_time < cutoff_time:
                    shutil.rmtree(item_path)
                    removed_dirs.append(item)
                    
                    # Also remove zip if it exists
                    zip_path = f"{item_path}.zip"
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                        
        return removed_dirs


conversion_service = ConversionService()
