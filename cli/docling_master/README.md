
Attempt 1
docling data/complex_pdfs/Complex1.pdf --to md --pipeline vlm --vlm-model smoldocling --device cuda --output docling_master  --->  some issues. 
  
Attempt 2
  docling data/complex_pdfs/Complex1.pdf \
    --to md \
    --pipeline vlm \
    --vlm-model smoldocling \
    --device cuda \
    --output docling_master \
    --table-mode accurate \
    --ocr \
    --enrich-formula \
    --enrich-picture-description \
    --verbose


Attempt 2
  docling data/complex_pdfs/Complex1.pdf \
    --to md \
    --pipeline vlm \
    --vlm-model smoldocling \
    --device cuda \
    --output docling_master \
    --table-mode accurate \
    --ocr \
    --enrich-formula \
    --enrich-picture-description \
    --image-export-mode placeholder \
    --verbose



  docling docling_master/image.png \
    --to md \
    --pipeline vlm \
    --vlm-model smoldocling \
    --device cuda \
    --output docling_master/image_output \
    --enrich-picture-description \
    --ocr \
    --enrich-formula \
    --table-mode accurate \
    --verbose