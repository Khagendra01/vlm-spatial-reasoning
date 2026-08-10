# Stage + zip the anonymized code archive for the WACV 2027 submission.
import os
import re
import shutil
import zipfile

ROOT = r'C:\Users\Khage\AppData\Local\Temp\opencode\pdv'
STAGE = os.path.join(ROOT, 'submission', 'wacv2027', 'code_stage')

shutil.rmtree(STAGE, ignore_errors=True)

CHDIR_OLD = 'os.chdir("/home/ubuntu/vlm-spatial-reasoning")'
CHDIR_NEW = ('ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n'
             'os.chdir(ROOT)')

SCRIPTS = ['build_canonical_tables.py', 'compare_site_zeroshot_lora.py',
           'site_confound_analysis.py', 'consistency_verdict_table.py',
           'make_paper_figures.py', 'make_publication_figures.py',
           'clean_label_orientation.py', 'two_stage_reasoning.py']
for s in SCRIPTS:
    src = os.path.join(ROOT, 'scripts', s)
    dst = os.path.join(STAGE, 'scripts', s)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    t = open(src, encoding='utf-8').read()
    t = t.replace(CHDIR_OLD, CHDIR_NEW)
    open(dst, 'w', encoding='utf-8').write(t)

src = os.path.join(ROOT, 'src', 'datasets', 'site.py')
dst = os.path.join(STAGE, 'src', 'datasets', 'site.py')
os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copy2(src, dst)

# results/ artifacts (small, CPU-reproducible)
RESULT_FILES = [
    'results/tables/vsr_conditions_table.csv', 'results/tables/vsr_conditions_table.md',
    'results/tables/site_validation_table.csv', 'results/tables/site_validation_table.md',
    'results/tables/orientation_clean_label_table.md',
    'results/site/site_protocol.json', 'results/site/run_metadata.json',
    'results/site/zeroshot_7b_predictions.csv', 'results/site/vsr_lora_predictions.csv',
    'results/site/zeroshot_image_metrics.json', 'results/site/vsr_lora_vs_zeroshot.json',
    'results/site/orientation_confound_analysis.json', 'results/site/orientation_confound_report.md',
    'results/probe/probe_results.json', 'results/probe/patch_probe_results.json',
    'results/probe/grounded_probe_results.json', 'results/probe/clear_subset_results.json',
    'results/probe/grounded_boxes.json',
    'results/consistency_verdict_table.json', 'results/consistency_verdict_table.md',
    'results/consistency_stats_7B_zero_shot.json', 'results/consistency_stats_LM_only_LoRA.json',
    'results/consistency_stats_hardneg_LoRA.json', 'results/consistency_stats_projector_LoRA.json',
    'results/consistency_stats_vision_proj_LoRA.json',
    'results/two_stage_results.json', 'results/vision_side_comparison.json',
    'results/orientation_analysis.json',
    'results/smolvlm2_metrics_2195_20260808_214536.json',
    'results/smolvlm2_structured_metrics_2195_20260808_225009.json',
    'results/general_lora_metrics_20260809_054915.json',
    'results/targeted_lora_metrics_20260809_061231.json',
    'results/qwen2vl_7b_metrics_20260809_064919.json',
    'results/7B_general_lora_metrics_20260809_094930.json',
    'results/7B_targeted_lora_metrics_20260809_095926.json',
    'results/7B_hardneg_lora_metrics_20260809_164619.json',
    'results/qwen2vl_7b_projector_lora_metrics_20260809_221720.json',
    'results/qwen2vl_7b_vision_proj_lora_metrics_20260809_222845.json',
    'results/smolvlm2_baseline_2195_20260808_214536.csv',
    'results/smolvlm2_structured_2195_20260808_225009.csv',
    'results/general_lora_predictions_20260809_054915.csv',
    'results/targeted_lora_predictions_20260809_061231.csv',
    'results/qwen2vl_7b_predictions_20260809_064919.csv',
    'results/7B_general_lora_predictions_20260809_094930.csv',
    'results/7B_targeted_lora_predictions_20260809_095926.csv',
    'results/7B_hardneg_lora_predictions_20260809_164619.csv',
    'results/qwen2vl_7b_projector_lora_predictions_20260809_221720.csv',
    'results/qwen2vl_7b_vision_proj_lora_predictions_20260809_222845.csv',
]
for rel in RESULT_FILES:
    src = os.path.join(ROOT, rel)
    dst = os.path.join(STAGE, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(src):
        print('MISSING:', rel)
        continue
    shutil.copy2(src, dst)

print('staged; scripts:', len(os.listdir(os.path.join(STAGE, 'scripts'))),
      '| result files:', len(RESULT_FILES))
