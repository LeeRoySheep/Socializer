#!/usr/bin/env python3
"""
Favicon Generator Script
========================

PURPOSE:
    Generate PNG favicons in all required sizes from the SVG source.
    Ensures consistent pigeon logo across all platforms and browsers.

USAGE:
    python scripts/generate_favicons.py

REQUIREMENTS:
    - cairosvg: pip install cairosvg
    - Pillow: pip install Pillow

OUTPUTS:
    - favicon.ico (16x16, 32x32, 48x48 multi-resolution)
    - favicon-16x16.png
    - favicon-32x32.png
    - apple-touch-icon.png (180x180)
    - android-chrome-192x192.png
    - android-chrome-512x512.png

OOP PRINCIPLES:
    - Single Responsibility: Each method handles one conversion task
    - Open/Closed: Easy to extend with new sizes
    - Dependency Injection: Paths configurable

AUTHOR: Socializer Team
DATE: 2025-12-11
"""

import os
from pathlib import Path
from typing import List, Tuple

try:
    import cairosvg
    from PIL import Image
    import io
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install cairosvg Pillow")
    exit(1)


class FaviconGenerator:
    """
    Generates favicon files in multiple formats and sizes.
    
    This class follows OOP best practices:
    - Encapsulation: All favicon generation logic in one place
    - Single Responsibility: Only handles favicon generation
    - Clear interfaces: Simple public methods
    
    Attributes:
        svg_path (Path): Path to source SVG file
        output_dir (Path): Directory for generated favicons
        sizes (List[Tuple[str, int]]): List of (filename, size) tuples
    
    Example:
        >>> generator = FaviconGenerator()
        >>> generator.generate_all()
        ✅ Generated 6 favicon files
    """
    
    def __init__(
        self, 
        svg_path: str = "static/favicon.svg",
        output_dir: str = "static"
    ):
        """
        Initialize the favicon generator.
        
        Args:
            svg_path: Path to source SVG file (relative to project root)
            output_dir: Output directory for generated files
        """
        self.project_root = Path(__file__).parent.parent
        self.svg_path = self.project_root / svg_path
        self.output_dir = self.project_root / output_dir
        
        # Define all required sizes: (filename, size_pixels)
        self.sizes: List[Tuple[str, int]] = [
            ("favicon-16x16.png", 16),
            ("favicon-32x32.png", 32),
            ("apple-touch-icon.png", 180),
            ("android-chrome-192x192.png", 192),
            ("android-chrome-512x512.png", 512),
        ]
        
    def validate_svg_exists(self) -> bool:
        """
        Validate that the source SVG file exists.
        
        Returns:
            bool: True if SVG exists, False otherwise
            
        Raises:
            FileNotFoundError: If SVG file is missing
        """
        if not self.svg_path.exists():
            raise FileNotFoundError(
                f"SVG source not found: {self.svg_path}\n"
                f"Please ensure favicon.svg exists in {self.output_dir}"
            )
        return True
    
    def svg_to_png(self, output_path: Path, size: int) -> None:
        """
        Convert SVG to PNG at specified size.
        
        Args:
            output_path: Path where PNG should be saved
            size: Size in pixels (width and height, square)
            
        Note:
            Uses cairosvg for high-quality SVG rasterization
        """
        cairosvg.svg2png(
            url=str(self.svg_path),
            write_to=str(output_path),
            output_width=size,
            output_height=size
        )
        
    def generate_ico(self) -> None:
        """
        Generate multi-resolution .ico file.
        
        Creates favicon.ico with embedded 16x16, 32x32, and 48x48 images
        for maximum browser compatibility.
        """
        ico_path = self.output_dir / "favicon.ico"
        sizes_for_ico = [16, 32, 48]
        images = []
        
        for size in sizes_for_ico:
            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(
                url=str(self.svg_path),
                output_width=size,
                output_height=size
            )
            img = Image.open(io.BytesIO(png_data))
            images.append(img)
        
        # Save as multi-resolution ICO
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )
        print(f"   ✅ favicon.ico (16x16, 32x32, 48x48)")
    
    def generate_pngs(self) -> None:
        """
        Generate all PNG favicon sizes.
        
        Iterates through self.sizes and creates each PNG file.
        """
        for filename, size in self.sizes:
            output_path = self.output_dir / filename
            self.svg_to_png(output_path, size)
            print(f"   ✅ {filename} ({size}x{size})")
    
    def generate_all(self) -> None:
        """
        Generate all favicon files.
        
        Main entry point that:
        1. Validates SVG exists
        2. Generates all PNG sizes
        3. Generates ICO file
        4. Reports success
        """
        print("🎨 Generating favicons from SVG...")
        print(f"📁 Source: {self.svg_path}")
        print(f"📁 Output: {self.output_dir}\n")
        
        # Validate
        self.validate_svg_exists()
        
        # Generate all files
        self.generate_pngs()
        self.generate_ico()
        
        print(f"\n✅ Successfully generated {len(self.sizes) + 1} favicon files!")
        print("\n📝 Next steps:")
        print("   1. Verify favicons appear in your browser")
        print("   2. Test on mobile devices (iOS/Android)")
        print("   3. Check PWA installation works correctly")


def main():
    """
    Main entry point for favicon generation.
    
    Creates FaviconGenerator instance and generates all files.
    """
    try:
        generator = FaviconGenerator()
        generator.generate_all()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
