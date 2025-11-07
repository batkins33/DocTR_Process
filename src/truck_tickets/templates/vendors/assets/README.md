# Vendor Logo Templates

This directory contains logo template images for vendor detection using OpenCV template matching.

## Directory Structure

```
assets/
├── README.md (this file)
├── wm_logo.png          # Waste Management Lewisville logo
├── ldi_logo.png         # LDI Yard logo
└── post_oak_logo.png    # Post Oak Pit logo
```

## Logo Template Requirements

### Image Format
- **Format**: PNG (preferred) or JPG
- **Color**: Grayscale or RGB (converted to grayscale during processing)
- **Size**: Typically 100-200px wide, 50-100px tall
- **Resolution**: 72-150 DPI

### Quality Guidelines
1. **High contrast**: Logo should have clear edges and distinct features
2. **Clean background**: Minimal noise or artifacts
3. **Consistent orientation**: Logo should be upright and level
4. **Representative**: Should match typical appearance on tickets

### Creating Logo Templates

#### From Existing Tickets
1. Open a high-quality ticket scan
2. Crop the logo region (include minimal surrounding whitespace)
3. Resize if needed (maintain aspect ratio)
4. Save as PNG with descriptive name

#### Using Image Editing Tools
```python
from PIL import Image

# Load ticket image
ticket = Image.open("sample_ticket.pdf")

# Crop logo region (adjust coordinates as needed)
logo = ticket.crop((10, 10, 210, 110))  # x1, y1, x2, y2

# Save as template
logo.save("wm_logo.png")
```

## Template Matching Configuration

Logo templates are referenced in vendor YAML files:

```yaml
logo:
  type: "image_template"
  path: "assets/wm_logo.png"  # Relative to templates/vendors/
  roi:
    x: 0
    y: 0
    width: 200
    height: 100
  threshold: 0.85  # Confidence threshold (0.0-1.0)
  method: "template_match"
```

### Parameters

- **path**: Path to logo template image (relative to templates/vendors/ or absolute)
- **roi**: Region of Interest on ticket where logo is expected
  - `x, y`: Top-left corner coordinates (pixels)
  - `width, height`: ROI dimensions (pixels)
- **threshold**: Minimum confidence score for positive match (0.0-1.0)
  - 0.85-0.95: High confidence (recommended)
  - 0.70-0.85: Medium confidence
  - < 0.70: Low confidence (may have false positives)
- **method**: Matching algorithm
  - `template_match`: OpenCV template matching (default)
  - `feature_match`: Feature-based matching (future)

## Testing Logo Templates

### Quick Test
```python
from truck_tickets.extractors import LogoDetector
from PIL import Image

# Initialize detector
detector = LogoDetector()

# Load template
detector.load_template(
    vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
    template_path="assets/wm_logo.png",
    roi={"x": 0, "y": 0, "width": 200, "height": 100},
    threshold=0.85
)

# Test on sample ticket
ticket_image = Image.open("sample_ticket.pdf")
vendor, confidence = detector.detect(ticket_image)

print(f"Detected: {vendor} (confidence: {confidence:.3f})")
```

### Integration Test
```bash
# Run logo detection tests
pytest tests/test_logo_detector.py -v

# Run with specific vendor
pytest tests/test_logo_detector.py::TestLogoDetector::test_detect_with_matching_logo -v
```

## Troubleshooting

### Low Confidence Scores

**Problem**: Logo detection returns confidence < threshold

**Solutions**:
1. **Adjust ROI**: Ensure ROI covers logo location on all tickets
2. **Improve template quality**: Use cleaner, higher-contrast template
3. **Lower threshold**: Reduce threshold to 0.75-0.80 (test for false positives)
4. **Try multi-scale**: Use `detect_multi_scale()` for varying resolutions

### False Positives

**Problem**: Wrong vendor detected or detection on non-logo regions

**Solutions**:
1. **Increase threshold**: Raise to 0.90-0.95 for stricter matching
2. **Narrow ROI**: Reduce ROI size to specific logo location
3. **Improve template**: Use more distinctive logo features
4. **Add vendor filter**: Limit detection to expected vendors

### No Detection

**Problem**: Logo not detected even with low threshold

**Solutions**:
1. **Check ROI**: Verify logo is within specified ROI
2. **Check template**: Ensure template image loads correctly
3. **Check image quality**: Verify ticket scan is clear and readable
4. **Enable logging**: Set log level to DEBUG for detailed output

## Performance Optimization

### Template Size
- Smaller templates (50-100px) are faster
- Larger templates (150-200px) are more accurate
- Balance based on ticket resolution

### ROI Size
- Smaller ROI = faster processing
- Larger ROI = more robust to logo position variation
- Typical: 200x100 to 400x200 pixels

### Multi-Scale Detection
- Use for tickets with varying resolutions
- Slower but more robust
- Recommended scales: [0.8, 1.0, 1.2]

## Adding New Vendor Logos

1. **Extract logo from sample ticket**
2. **Save to assets/ directory**
3. **Update vendor YAML file** with logo configuration
4. **Test detection** on sample tickets
5. **Adjust threshold** based on results
6. **Document** in this README

## Notes

- Logo templates are optional; keyword matching is always available as fallback
- Multiple vendors can share similar logos (confidence scores differentiate)
- Logo detection is disabled if no image is provided to `VendorDetector.detect()`
- Templates are loaded once at initialization for performance

---

**Last Updated**: November 7, 2025
**Maintained By**: Development Team
