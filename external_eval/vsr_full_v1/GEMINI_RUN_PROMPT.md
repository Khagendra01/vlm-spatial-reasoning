# Gemini evaluation prompt — VSR full test set (2,195 images)

You are performing a blind, scientific evaluation of vision–language spatial reasoning. The images are in this Google Drive folder:

https://drive.google.com/drive/folders/1cnqO6elektYOg50GFGh_zdD8VqQEyqI9?usp=sharing

Each file is named id<item_id>.jpg (for example, id7.jpg). The image filename corresponds exactly to the `item_id` column of the CSV files below, which are also uploaded to the same folder:

- vsr_2195.csv — columns: item_id, relation, statement, image_url
- consistency_pairs.csv — columns: pair_id, family, item_id, statement_a, statement_b, image_url

IMPORTANT: The CSV files contain ONLY the image id, the relation name, and the statement. They deliberately do NOT contain the correct answers. Do not search for, infer, or use any ground-truth labels, model predictions, or prior annotations from any source. Judge each statement strictly from its image.

There are TWO passes. Run the Binary Audit first, then the Consistency pass.

=== PASS 1: BINARY AUDIT (all 2,195 items) ===

Read vsr_2195.csv. For every row, open the file images/id<item_id>.jpg and answer the statement with the frozen prompt below, exactly as written, one image per request:

Look at the image carefully.

Statement: "<statement>"

Is this statement true or false?

Answer with exactly one word: True or False.

Rules:
- Respond with exactly one word: True, or False. Nothing else.
- If the image is missing, unreadable, or the model cannot produce a single unambiguously binary verdict, output INVALID and state the reason in the invalid_reason column. Never guess, never elaborate.
- Use the lowest available reasoning/thinking setting for the primary run. If your interface does not expose a setting, note that in your report.
- Preserve the model's raw response verbatim in raw_response.
- Do not skip items. All 2,195 items must have a row.

Output CSV format (save as: gemini_vsr_2195_results.csv):

run_id,model_id,provider,eval_date_utc,item_id,relation,raw_response,parsed_binary,invalid_reason,latency_ms

parsed_binary must be exactly True, False, or INVALID.

=== PASS 2: CONSISTENCY PASS (696 complementary pairs) ===

Read consistency_pairs.csv. Each row defines one complementary pair: statement_a and statement_b describe the SAME image (same item_id) with complementary relations (e.g., "The cat is facing the dog." vs "The cat is facing away from the dog."). For every row:

1. Open images/id<item_id>.jpg.
2. Ask statement_a with the frozen prompt above, exactly one request. Record the answer.
3. Ask statement_b with the frozen prompt above, in a SEPARATE request (never show both statements at once). Record the answer.

Output CSV format (save as: gemini_consistency_pairs_results.csv):

run_id,model_id,provider,eval_date_utc,pair_id,family,item_id,part,raw_response,parsed_binary,invalid_reason,latency_ms

- part is a for statement_a and b for statement_b.
- parsed_binary: True, False, or INVALID, per the same rules.
- family tells you the relation family: FF = facing/facing-away, FB = front/behind, LR = left/right, PP = parallel/perpendicular (treat PP as a soft complement; still answer both statements).
- All 696 pairs x 2 parts = 1,392 rows must be present.

=== REPORT ===

When finished, produce a short report including:
- model identifier and version actually used
- evaluation date and time (UTC)
- reasoning/thinking setting used, or "not exposed"
- image handling (original resolution, any downscaling)
- total requests, any retries or failures, and how long the run took
- the number of INVALID outputs in each pass and their reasons

Deliverables: the two CSV files (gemini_vsr_2195_results.csv, gemini_consistency_pairs_results.csv) with one row per item, every item answered, raw responses preserved, and the report. Do not compute or report accuracy — scoring will be done on our side against the official ground truth.
