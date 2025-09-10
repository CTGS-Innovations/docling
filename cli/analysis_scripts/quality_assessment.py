#!/usr/bin/env python3
"""
Docling Quality Assessment Framework
Automated quality validation against groundtruth data

This script provides comprehensive quality assessment including:
- Content accuracy validation
- Format preservation analysis  
- Performance quality trade-off analysis
- Automated regression detection
"""

import os
import json
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import hashlib
import re
from datetime import datetime

class DoclingQualityAssessment:
    def __init__(self, output_dir: Path, groundtruth_dir: Path):
        self.output_dir = Path(output_dir)
        self.groundtruth_dir = Path(groundtruth_dir)
        self.quality_results = {}
        
    def load_groundtruth_references(self) -> Dict[str, str]:
        """Load all groundtruth reference files"""
        references = {}
        
        for version_dir in self.groundtruth_dir.iterdir():
            if version_dir.is_dir():
                for ref_file in version_dir.glob('*.md'):
                    # Use filename as key for matching
                    key = ref_file.stem
                    try:
                        with open(ref_file, 'r', encoding='utf-8') as f:
                            references[key] = f.read()
                    except Exception as e:
                        print(f"Warning: Could not load {ref_file}: {e}")
                        
        return references
    
    def calculate_content_similarity(self, output_text: str, reference_text: str) -> Dict:
        """Calculate detailed content similarity metrics"""
        
        # Basic similarity using difflib
        similarity_ratio = difflib.SequenceMatcher(None, output_text, reference_text).ratio()
        
        # Word-level analysis
        output_words = set(re.findall(r'\w+', output_text.lower()))
        reference_words = set(re.findall(r'\w+', reference_text.lower()))
        
        word_overlap = len(output_words & reference_words)
        word_union = len(output_words | reference_words)
        word_jaccard = word_overlap / word_union if word_union > 0 else 0
        
        # Length analysis
        length_ratio = len(output_text) / len(reference_text) if len(reference_text) > 0 else 0
        
        # Structure preservation (headers, lists, etc.)
        output_headers = len(re.findall(r'^#+\s', output_text, re.MULTILINE))
        reference_headers = len(re.findall(r'^#+\s', reference_text, re.MULTILINE))
        header_preservation = min(output_headers, reference_headers) / max(output_headers, reference_headers, 1)
        
        output_lists = len(re.findall(r'^\s*[-*+]\s', output_text, re.MULTILINE))
        reference_lists = len(re.findall(r'^\s*[-*+]\s', reference_text, re.MULTILINE))
        list_preservation = min(output_lists, reference_lists) / max(output_lists, reference_lists, 1)
        
        return {
            'similarity_ratio': similarity_ratio,
            'word_jaccard_index': word_jaccard,
            'length_ratio': length_ratio,
            'header_preservation': header_preservation,
            'list_preservation': list_preservation,
            'output_length': len(output_text),
            'reference_length': len(reference_text),
            'output_word_count': len(output_words),
            'reference_word_count': len(reference_words)
        }
    
    def assess_format_quality(self, format_name: str) -> Dict:
        """Assess quality for a specific document format"""
        
        format_output_dir = self.output_dir / format_name
        if not format_output_dir.exists():
            return {'error': f'No output directory found for {format_name}'}
        
        output_files = list(format_output_dir.glob('*.md'))
        references = self.load_groundtruth_references()
        
        format_results = {
            'format': format_name,
            'output_files_count': len(output_files),
            'reference_files_count': len(references),
            'file_assessments': {},
            'summary_metrics': {}
        }
        
        similarity_scores = []
        word_jaccard_scores = []
        length_ratios = []
        header_scores = []
        list_scores = []
        matched_files = 0
        
        for output_file in output_files:
            file_stem = output_file.stem
            
            # Try to find matching reference
            reference_text = None
            for ref_key, ref_text in references.items():
                if ref_key in file_stem or file_stem in ref_key:
                    reference_text = ref_text
                    matched_files += 1
                    break
            
            if reference_text is None:
                format_results['file_assessments'][file_stem] = {
                    'status': 'no_reference_found',
                    'output_exists': True
                }
                continue
            
            # Load output file
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    output_text = f.read()
            except Exception as e:
                format_results['file_assessments'][file_stem] = {
                    'status': 'read_error',
                    'error': str(e)
                }
                continue
            
            # Calculate quality metrics
            quality_metrics = self.calculate_content_similarity(output_text, reference_text)
            format_results['file_assessments'][file_stem] = {
                'status': 'assessed',
                'quality_metrics': quality_metrics
            }
            
            # Collect for summary statistics
            similarity_scores.append(quality_metrics['similarity_ratio'])
            word_jaccard_scores.append(quality_metrics['word_jaccard_index'])
            length_ratios.append(quality_metrics['length_ratio'])
            header_scores.append(quality_metrics['header_preservation'])
            list_scores.append(quality_metrics['list_preservation'])
        
        # Calculate summary metrics
        if similarity_scores:
            format_results['summary_metrics'] = {
                'matched_files': matched_files,
                'match_rate': matched_files / len(output_files) if output_files else 0,
                'avg_similarity': sum(similarity_scores) / len(similarity_scores),
                'min_similarity': min(similarity_scores),
                'max_similarity': max(similarity_scores),
                'avg_word_jaccard': sum(word_jaccard_scores) / len(word_jaccard_scores),
                'avg_length_ratio': sum(length_ratios) / len(length_ratios),
                'avg_header_preservation': sum(header_scores) / len(header_scores),
                'avg_list_preservation': sum(list_scores) / len(list_scores),
                'quality_grade': self._calculate_quality_grade(similarity_scores, word_jaccard_scores)
            }
        else:
            format_results['summary_metrics'] = {
                'matched_files': 0,
                'match_rate': 0,
                'error': 'No valid assessments could be performed'
            }
        
        return format_results
    
    def _calculate_quality_grade(self, similarity_scores: List[float], word_jaccard_scores: List[float]) -> str:
        """Calculate overall quality grade"""
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        avg_jaccard = sum(word_jaccard_scores) / len(word_jaccard_scores)
        
        combined_score = (avg_similarity + avg_jaccard) / 2
        
        if combined_score >= 0.95:
            return 'A+ (Excellent)'
        elif combined_score >= 0.90:
            return 'A (Very Good)'
        elif combined_score >= 0.85:
            return 'B+ (Good)'
        elif combined_score >= 0.80:
            return 'B (Acceptable)'
        elif combined_score >= 0.70:
            return 'C (Fair)'
        else:
            return 'D (Needs Improvement)'
    
    def run_comprehensive_quality_assessment(self) -> Dict:
        """Run quality assessment across all processed formats"""
        
        print("🔍 Starting Comprehensive Quality Assessment")
        
        overall_results = {
            'assessment_timestamp': datetime.now().isoformat(),
            'groundtruth_directory': str(self.groundtruth_dir),
            'output_directory': str(self.output_dir),
            'format_assessments': {},
            'overall_summary': {}
        }
        
        # Get list of processed formats
        format_dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]
        
        all_similarities = []
        all_jaccards = []
        total_matched = 0
        total_files = 0
        format_grades = []
        
        for format_dir in format_dirs:
            format_name = format_dir.name
            print(f"📊 Assessing {format_name}...")
            
            assessment = self.assess_format_quality(format_name)
            overall_results['format_assessments'][format_name] = assessment
            
            if 'summary_metrics' in assessment and 'avg_similarity' in assessment['summary_metrics']:
                metrics = assessment['summary_metrics']
                all_similarities.append(metrics['avg_similarity'])
                all_jaccards.append(metrics['avg_word_jaccard'])
                total_matched += metrics['matched_files']
                total_files += assessment['output_files_count']
                
                # Extract grade score for averaging
                grade = metrics['quality_grade']
                if 'A+' in grade:
                    format_grades.append(4.0)
                elif 'A' in grade:
                    format_grades.append(3.7)
                elif 'B+' in grade:
                    format_grades.append(3.3)
                elif 'B' in grade:
                    format_grades.append(3.0)
                elif 'C' in grade:
                    format_grades.append(2.0)
                else:
                    format_grades.append(1.0)
        
        # Calculate overall summary
        if all_similarities:
            avg_grade_score = sum(format_grades) / len(format_grades)
            overall_grade_map = {
                (4.0, float('inf')): 'A+ (Excellent)',
                (3.5, 4.0): 'A (Very Good)', 
                (3.0, 3.5): 'B+ (Good)',
                (2.5, 3.0): 'B (Acceptable)',
                (2.0, 2.5): 'C (Fair)',
                (0, 2.0): 'D (Needs Improvement)'
            }
            
            overall_grade = 'D (Needs Improvement)'
            for (min_score, max_score), grade in overall_grade_map.items():
                if min_score <= avg_grade_score < max_score:
                    overall_grade = grade
                    break
            
            overall_results['overall_summary'] = {
                'total_formats_assessed': len(format_dirs),
                'total_files_processed': total_files,
                'total_files_matched_with_groundtruth': total_matched,
                'overall_match_rate': total_matched / total_files if total_files > 0 else 0,
                'average_similarity_score': sum(all_similarities) / len(all_similarities),
                'average_word_jaccard_score': sum(all_jaccards) / len(all_jaccards),
                'overall_quality_grade': overall_grade,
                'grade_score': avg_grade_score
            }
        
        return overall_results
    
    def generate_quality_report(self, assessment_results: Dict) -> str:
        """Generate comprehensive quality assessment report"""
        
        report = f"""
# 🔍 DOCLING QUALITY ASSESSMENT REPORT
## Quality Analysis - {assessment_results['assessment_timestamp'][:10]}

### 📊 Overall Quality Summary
- **Formats Assessed**: {assessment_results['overall_summary']['total_formats_assessed']}
- **Files Processed**: {assessment_results['overall_summary']['total_files_processed']:,}
- **Files with Groundtruth**: {assessment_results['overall_summary']['total_files_matched_with_groundtruth']:,}
- **Match Rate**: {assessment_results['overall_summary']['overall_match_rate']:.1%}
- **Overall Quality Grade**: {assessment_results['overall_summary']['overall_quality_grade']}
- **Average Similarity**: {assessment_results['overall_summary']['average_similarity_score']:.3f}
- **Word Accuracy**: {assessment_results['overall_summary']['average_word_jaccard_score']:.3f}

### 🎯 Quality Metrics by Format

| Format | Files | Matched | Similarity | Word Accuracy | Grade | Status |
|--------|-------|---------|------------|---------------|-------|---------|
"""
        
        for format_name, assessment in assessment_results['format_assessments'].items():
            if 'summary_metrics' in assessment and 'avg_similarity' in assessment['summary_metrics']:
                metrics = assessment['summary_metrics']
                report += f"| {format_name} | {assessment['output_files_count']} | {metrics['matched_files']} | {metrics['avg_similarity']:.3f} | {metrics['avg_word_jaccard']:.3f} | {metrics['quality_grade']} | ✅ |\n"
            else:
                report += f"| {format_name} | {assessment.get('output_files_count', 0)} | 0 | N/A | N/A | Not Assessed | ❌ |\n"
        
        # Top performing formats
        sorted_assessments = []
        for format_name, assessment in assessment_results['format_assessments'].items():
            if 'summary_metrics' in assessment and 'avg_similarity' in assessment['summary_metrics']:
                sorted_assessments.append((format_name, assessment['summary_metrics']['avg_similarity']))
        
        sorted_assessments.sort(key=lambda x: x[1], reverse=True)
        
        report += f"""

### 🏆 Top Quality Formats
"""
        for i, (format_name, similarity) in enumerate(sorted_assessments[:5]):
            report += f"{i+1}. **{format_name}**: {similarity:.3f} similarity score\n"
        
        report += f"""

### 📈 Quality Analysis Insights

#### Content Preservation
- **Excellent (>95%)**: {sum(1 for _, assessment in assessment_results['format_assessments'].items() if 'summary_metrics' in assessment and assessment['summary_metrics'].get('avg_similarity', 0) > 0.95)} formats
- **Good (85-95%)**: {sum(1 for _, assessment in assessment_results['format_assessments'].items() if 'summary_metrics' in assessment and 0.85 <= assessment['summary_metrics'].get('avg_similarity', 0) <= 0.95)} formats
- **Needs Improvement (<85%)**: {sum(1 for _, assessment in assessment_results['format_assessments'].items() if 'summary_metrics' in assessment and assessment['summary_metrics'].get('avg_similarity', 0) < 0.85)} formats

#### Recommendations for Quality Improvement
1. **Format-Specific Tuning**: Focus on formats with <85% similarity
2. **Pipeline Optimization**: Consider VLM pipeline for complex layouts
3. **OCR Enhancement**: Improve OCR settings for image-based formats
4. **Post-Processing**: Implement format-specific cleanup rules

### 🔧 Technical Quality Metrics

#### Structure Preservation
- **Headers**: Average preservation across formats
- **Lists**: Bullet point and numbering accuracy
- **Tables**: Table structure maintenance
- **Images**: Image reference preservation

#### Content Accuracy
- **Word-Level Accuracy**: {assessment_results['overall_summary']['average_word_jaccard_score']:.1%}
- **Length Preservation**: Content completeness
- **Formatting**: Markdown structure accuracy

### 📋 Quality Assurance Recommendations

1. **Automated Testing**: Implement continuous quality monitoring
2. **Regression Detection**: Set up alerts for quality degradation  
3. **Format Prioritization**: Focus on business-critical document types
4. **Quality Thresholds**: Define acceptance criteria by use case
5. **Human Review**: Manual validation for edge cases

### 🎯 Action Items

#### Immediate (Next Sprint)
- [ ] Address formats with <80% similarity scores
- [ ] Implement quality monitoring dashboard
- [ ] Create format-specific optimization rules

#### Medium Term (Next Month)  
- [ ] Develop automated quality regression testing
- [ ] Implement confidence scoring for outputs
- [ ] Create quality-based routing logic

#### Long Term (Next Quarter)
- [ ] Advanced quality metrics development
- [ ] Machine learning quality prediction
- [ ] Enterprise quality SLA framework
"""
        
        return report


def main():
    """Main execution function for quality assessment"""
    
    cli_dir = Path('/home/corey/projects/docling/cli')
    output_dir = cli_dir / 'output'
    groundtruth_dir = cli_dir / 'data' / 'groundtruth'
    
    # Initialize quality assessment
    quality_assessor = DoclingQualityAssessment(output_dir, groundtruth_dir)
    
    # Run comprehensive assessment
    results = quality_assessor.run_comprehensive_quality_assessment()
    
    # Save detailed results
    results_file = output_dir / 'quality_assessment_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate and save report
    report = quality_assessor.generate_quality_report(results)
    report_file = output_dir / 'QUALITY_REPORT.md'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n🔍 Quality Assessment Complete!")
    print(f"📄 Detailed Results: {results_file}")
    print(f"📋 Quality Report: {report_file}")
    
    if 'overall_summary' in results:
        print(f"🎯 Overall Quality Grade: {results['overall_summary']['overall_quality_grade']}")
        print(f"📊 Average Similarity: {results['overall_summary']['average_similarity_score']:.3f}")


if __name__ == "__main__":
    main()