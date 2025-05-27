#!/usr/bin/env python3
"""
Simple graph viewer for RocksDB Write Buffer Size optimization results
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os

def view_graphs():
    """Display all generated graphs."""
    
    # Find all PNG files
    png_files = [f for f in os.listdir('.') if f.endswith('.png')]
    
    if not png_files:
        print("❌ No PNG files found in current directory")
        return
    
    print(f"📊 Found {len(png_files)} graph files:")
    for i, file in enumerate(png_files, 1):
        print(f"  {i}. {file}")
    
    print("\n" + "="*60)
    
    # Display each graph
    for png_file in sorted(png_files):
        print(f"\n📈 Displaying: {png_file}")
        
        try:
            # Read and display image
            img = mpimg.imread(png_file)
            
            plt.figure(figsize=(16, 12))
            plt.imshow(img)
            plt.axis('off')
            plt.title(f'{png_file}', fontsize=16, fontweight='bold', pad=20)
            plt.tight_layout()
            
            # Save a copy with timestamp if needed
            plt.show()
            
        except Exception as e:
            print(f"❌ Error displaying {png_file}: {e}")
    
    print("\n✅ All graphs displayed successfully!")

if __name__ == "__main__":
    print("RocksDB Write Buffer Size Optimization - Graph Viewer")
    print("=" * 60)
    view_graphs() 