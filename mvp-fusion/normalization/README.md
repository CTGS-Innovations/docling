# MVP-Fusion Normalization Module

## Overview

Centralized normalization strategy for all NER entities following industry standards. This module implements a design pattern focused on efficiency and easy maintenance.

## Architecture

```
normalization/
├── __init__.py                 # Module interface and exports
├── canonical_units.yaml       # Industry-standard unit conversion map
├── measurement_normalizer.py  # Measurement normalization engine
├── README.md                  # This documentation
└── entity_normalizers/        # Future: entity-specific normalizers
    ├── person_normalizer.py   # Future: Person name normalization
    ├── org_normalizer.py      # Future: Organization normalization
    └── ...                    # Future: Other entity normalizers
```

## Design Principles

### 1. Single Source of Truth
- `canonical_units.yaml`: Definitive conversion rules for all measurement types
- No duplicate normalization logic across the codebase
- Centralized configuration for easy updates

### 2. Industry Standards Compliance
- Follows MVP-FUSION-NER.md PRD specifications
- Structured schema: `value`, `unit`, `text`, `type`, `span`, `normalized`
- 10 measurement categories with canonical units (meters, kg, liters, etc.)

### 3. Performance Optimization
- FLPC-compatible regex patterns for high-speed processing
- Target: 2000+ pages/sec processing speed
- Efficient patterns using `[0-9]` over `\d`, explicit alternations

### 4. Reusable Patterns
- Common normalization interface across all entity types
- Extensible architecture for future entity normalizers
- Backward compatibility with existing MVP-Fusion pipeline

## Usage

### Basic Measurement Normalization

```python
from normalization import MeasurementNormalizer

normalizer = MeasurementNormalizer()
measurements = normalizer.extract_measurements("The building is 50 feet tall and weighs 100 tons.")

for measurement in measurements:
    print(f"Original: {measurement.text}")
    print(f"Normalized: {measurement.normalized['value']} {measurement.normalized['unit']}")
```

### Integration with MVP-Fusion Pipeline

```python
from normalization import normalize_measurement_text

# Simple function interface for pipeline integration
normalized_measurements = normalize_measurement_text(content)
```

## Configuration

### Canonical Units

The `canonical_units.yaml` file defines:
- **Conversion factors** for all measurement types
- **Canonical target units** (meters, kg, °C, etc.)
- **FLPC-optimized regex patterns** for high performance
- **Special handling rules** (temperature formulas, currency codes)

### Supported Measurement Types

1. **Length** → meters (m)
2. **Weight** → kilograms (kg) 
3. **Volume** → liters (L)
4. **Temperature** → Celsius (°C)
5. **Angle** → radians (rad)
6. **Percentage** → ratio (0-1)
7. **Time** → seconds (s)
8. **Speed** → meters/second (m/s)
9. **Area** → square meters (m²)
10. **Currency** → ISO codes (USD, EUR, etc.)

## Extension Guidelines

### Adding New Entity Normalizers

1. Create new normalizer in `entity_normalizers/` directory
2. Follow the established pattern:
   - Load configuration from YAML
   - Implement extraction and normalization methods
   - Return structured schema with original + normalized data
3. Export through `__init__.py`
4. Update existing pipelines to use new normalizer

### Performance Considerations

- Keep regex patterns FLPC-compatible
- Use explicit alternations: `(feet|ft|inches|in)`
- Prefer `[0-9]` over `\d` for character matching
- Test performance impact with large documents
- Target <50ms processing per document

## Integration Points

### EntityNormalizer Integration
The existing `EntityNormalizer` class integrates with this module:
```python
from normalization import MeasurementNormalizer

def _normalize_measurement(self, value: str, span: Dict = None):
    normalizer = MeasurementNormalizer()
    # ... normalization logic
```

### Pipeline Integration
Update import paths in pipeline files:
```python
# Old
from knowledge.extractors.measurement_normalizer import MeasurementNormalizer

# New  
from normalization import MeasurementNormalizer
```

## Future Enhancements

- **Person Normalization**: Name canonicalization, title extraction
- **Organization Normalization**: Company name variants, acronym expansion  
- **Location Normalization**: Address standardization, geocoding
- **Date/Time Normalization**: Timezone handling, format standardization
- **Multi-language Support**: Internationalization of unit names
- **Real-time Currency**: Exchange rate integration for currency conversion