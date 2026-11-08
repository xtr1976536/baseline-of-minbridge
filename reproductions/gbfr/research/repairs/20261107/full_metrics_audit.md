# 全量已处理题评分与单位审计

覆盖 R19 已保存的全部1,401条；仅离线读记录，API调用0，不改预测、数据、金标或精度策略。

| 数据集 | 记录 | 旧正确 | 新评分正确 | 旧准确率 | 新评分准确率 | 恢复误判 | 新揭示冲突 |
|---|---:|---:|---:|---:|---:|---:|---:|
| FinQA | 731 | 511 | 522 | 69.90% | 71.41% | 11 | 0 |
| TAT-QA | 670 | 536 | 568 | 80.00% | 84.78% | 33 | 1 |

这些分数只表示同一批旧预测在修复后的评分器下重算，不能写成模型重新推理的改进。

## 已证实的代码问题

1. 金标明确`$17.6 million`或官方答案展示尺度被另一张输入表的`thousand`覆盖。展示单位必须与输入报告单位分开。
2. 通过子串在问题中找币种，把 Europe 误匹配成 EUR；已改用币种 token 词界。
3. `How many ...`条件计数和`Which year ...`年份返回被比较对象的货币、金额尺度、每股或百分比污染。
4. 问题明确`in $ millions`、`in US$ m`等输出格式未识别；输入提及的exercise price误把total option value当每股输出。
5. `proportion`、`per ordinary share`、`dollars per warrant`等单位表示不统一；`scale=ratio`导致实际程序正确后仍报错。
6. 只识别出一个表头单位时忽略内文明示的不同尺度，错误地把一个局部表头当成整页的答案单位。

## 不隐瞒降分样本

`TAT-QA:23b98a2dfcb8b787448e527f00cffa9b_720e234d5d8c898464ab864a2f524fff`：金标182,228、官方scale=million；源表明确in thousands，模型返回182228 thousand。按官方输出尺度优先，新评分计错。源标注自身存在冲突，未改标签保分。

## 分类边界

42条旧错误预测与金标原始数字按相同精度一致，仅作为候选筛查。源证据和正反测试支持的修复实际恢复44条（含若干原始数不同但明确单位换算后正确），并揭示1条原先误计对的标注矛盾。

110条可回答题误拒仍需修复执行链路；其余数值差异不能全部归因金标。完整分类、单位换算、全部翻转ID与源段落在同名JSON。

未跑到任何不可回答反事实，因此本批记录不能提供拒答准确率。

## 每条评分翻转

| 样本 | 旧→新 | 原因 | 金标 | 预测 |
|---|---|---|---:|---:|
| FinQA:ILMN/2008/page_82.pdf-1 | False→True | warrant_price_not_ordinary_share_price | 7.47 | 7.474549160109826 |
| FinQA:GPN/2010/page_89.pdf-3 | False→True | unrelated_input_price_or_reporting_scale | 26.8 | 26.799999999999997 |
| FinQA:AMT/2006/page_113.pdf-4 | False→True | unrelated_input_price_or_reporting_scale | 2.63 | 2.6333333333333333 |
| FinQA:PPG/2008/page_52.pdf-1 | False→True | explicit_question_output_scale | 120 | 120.0 |
| FinQA:JPM/2015/page_137.pdf-1 | False→True | unrelated_input_price_or_reporting_scale | -19.3 | -19.299999999999997 |
| FinQA:HWM/2018/page_96.pdf-1 | False→True | explicit_question_output_scale | 241.11 | 241.10999999999999 |
| FinQA:GPN/2013/page_87.pdf-2 | False→True | explicit_gold_display_unit_overridden_by_other_table | $ 13.4 million | 13.4 |
| FinQA:STT/2011/page_69.pdf-2 | False→True | unrelated_input_price_or_reporting_scale | 28000 | 28000.0 |
| FinQA:MRO/2007/page_136.pdf-1 | False→True | explicit_question_output_scale | 74 | 74.0 |
| FinQA:AMT/2012/page_50.pdf-2 | False→True | unrelated_input_price_or_reporting_scale | 7662592 | 7662592.0 |
| FinQA:AMT/2014/page_149.pdf-1 | False→True | explicit_question_output_scale | -4.7 | -4.700000000000001 |
| TAT-QA:5e5f8b76df669b1a32df3074c2c551be_635d756eb2458f9cb07ad2fc9ef5ce7a | False→True | requested_cardinality_vs_threshold_financial_quantity | 3 | 3.0 |
| TAT-QA:f4e5e687e6185cabde6d70a4d37f729f_c29b6258a24fcbbe12c294130ff18516 | False→True | explicit_gold_display_unit_overridden_by_other_table | $17.6 million | 17.6 |
| TAT-QA:bf3bb2fe848111c6f1370b66cdd8da3e_2964c5a70ef10a43b721dd66835612c8 | False→True | eur_substring_in_europe | 1869.5 | 1869.5 |
| TAT-QA:3e2109c375cbf670d40c77b22b430b20_c91185569a4dee8ffc347ca66f16797e | False→True | explicit_gold_display_unit_overridden_by_other_table | $923.4 million | 923.4 |
| TAT-QA:eedaff83a4efeb4d5ea9cfcc7664b56e_f9b4661a1bafc824ab65e2b0f06ff408 | False→True | explicit_gold_display_unit_overridden_by_other_table | $18.5 million | 18467.0 |
| TAT-QA:eedaff83a4efeb4d5ea9cfcc7664b56e_2cd91d7ed529bef7027c8b1874c74f58 | False→True | explicit_gold_display_unit_overridden_by_other_table | $8.3 million | 8.3 |
| TAT-QA:8f88cc6a1780582fa50c0b8318c2fb38_73cebb2620f32179ef0899312db1bb4a | False→True | official_answer_display_scale_priority | 5.7 | 5.7 |
| TAT-QA:504d01c4bb83fc6d346c56fee69948cc_287698fe88f19a7fdff20525435ead5b | False→True | requested_year_vs_compared_financial_quantity | 2019 | 2019.0 |
| TAT-QA:504d01c4bb83fc6d346c56fee69948cc_ff6211402b4a547aff3f4197073e0423 | False→True | unit_spelling_alias | 0.1 | 0.10000000000000009 |
| TAT-QA:23b98a2dfcb8b787448e527f00cffa9b_dacba996238131f4c27a870ce866bc31 | False→True | official_answer_display_scale_priority | 19.7 | 19.7 |
| TAT-QA:23b98a2dfcb8b787448e527f00cffa9b_bc0f5dc715ed31d9471b37d2dcbb5a99 | False→True | official_answer_display_scale_priority | 12.7 | 12.7 |
| TAT-QA:23b98a2dfcb8b787448e527f00cffa9b_720e234d5d8c898464ab864a2f524fff | True→False | official_answer_display_scale_priority | 182,228 | 182228.0 |
| TAT-QA:8b1c7617ae16b63840f3cfc52ea82824_1d5aea847254a9c3a9771b7b1a9ae40b | False→True | requested_year_vs_compared_financial_quantity | 2019 | 2019.0 |
| TAT-QA:0551beccb943904e051f6f2a1519bd3a_3b20cbd48416759c1c82b014f5c3514c | False→True | explicit_gold_display_unit_overridden_by_other_table | $12.8 million | 12.8 |
| TAT-QA:d014d1498874d83a9cadf694184173d5_f150122a8ccd8e76585d982c10a41e79 | False→True | explicit_gold_display_unit_overridden_by_other_table | $13.8 million | 13.8 |
| TAT-QA:d014d1498874d83a9cadf694184173d5_885f1bfaa095ac6a9776b2805cc818d0 | False→True | explicit_gold_display_unit_overridden_by_other_table | $12.4 million | 12.4 |
| TAT-QA:9082b05b2e0e2600d7f405f82795f041_e6c8eef8ea37699e9d8c1f6b5f50b451 | False→True | requested_cardinality_vs_threshold_financial_quantity | 1 | 1.0 |
| TAT-QA:3b4fab3751ab73cfc1ab93765c36c584_054db086be0c92381153e2b1fd9d5534 | False→True | explicit_gold_display_unit_overridden_by_other_table | $165.0 million | 165.0 |
| TAT-QA:6bcecf51179c59479764f84878ff238a_028c9022c69d88a2a9cbc5e9ac2ad2fc | False→True | explicit_gold_display_unit_overridden_by_other_table | $2.2 million | 2.2 |
| TAT-QA:6bcecf51179c59479764f84878ff238a_9f8cf40f681b7cb032a8daf0a641f823 | False→True | explicit_gold_display_unit_overridden_by_other_table | $3.8 million | 3.8 |
| TAT-QA:ce2ea049e35bd18c190d6f5676ec7d3d_54ae05dc3d1c2df122b4d2b36f8dace6 | False→True | explicit_gold_display_unit_overridden_by_other_table | US$6 million | 6.0 |
| TAT-QA:f5850c2764209f26fccf7923dd714ea4_f005fbea468ed191b98d44c447b868ba | False→True | explicit_gold_display_unit_overridden_by_other_table | $19.1 million | 19064.0 |
| TAT-QA:f5850c2764209f26fccf7923dd714ea4_bdf2411e367d4b93fb0247c42751491f | False→True | official_answer_display_scale_priority | 7 | 7.0 |
| TAT-QA:73842f616f18b30fe624ac4a4281a91d_109e88ae0baf844eb2b4c408623ae655 | False→True | explicit_gold_display_unit_overridden_by_other_table | $13.8 million | 13.8 |
| TAT-QA:2c24a027853e17b103ac055951cf35f2_7e5941aa85f6ed102e168f22724242d7 | False→True | explicit_gold_display_unit_overridden_by_other_table | $7.2 million | 7241.0 |
| TAT-QA:8a593a14363893b7570489580a9d0545_6874ed03a9170f15145d98ccf84e17d3 | False→True | official_answer_display_scale_priority | 9521.67 | 9521.666666666666 |
| TAT-QA:4ab898d6877c171a1e67f9be919c5e68_6dd8087f3eb7334e78512f7812d6b219 | False→True | explicit_gold_display_unit_overridden_by_other_table | $15.5 million | 15.5 |
| TAT-QA:6998ff3a821511af8a6c3d9b8c855502_34a544721ab7683ac3a3eb9109456529 | False→True | unit_spelling_alias | 0.65 | 0.6485052545658606 |
| TAT-QA:434b94166389d203839e681526978a7d_9aab1000cf8d1e140d933d7f1b5226c0 | False→True | explicit_gold_display_unit_overridden_by_other_table | $4.3 million | 4311.0 |
| TAT-QA:434b94166389d203839e681526978a7d_a483c4949ad7bd9ff28faf0d78540f3c | False→True | explicit_gold_display_unit_overridden_by_other_table | $0.5 million | 0.5 |
| TAT-QA:6ad2ec5c0b711b3fb827cb77b1ebecbe_b6b9d21c799743ac0c5566a4601a093d | False→True | explicit_gold_display_unit_overridden_by_other_table | $122.8 million | 122.8 |
| TAT-QA:6ad2ec5c0b711b3fb827cb77b1ebecbe_12817ae90e97e3e62659e5b8a8187963 | False→True | explicit_gold_display_unit_overridden_by_other_table | $124.4 million | 124.4 |
| TAT-QA:5e06ef4f2fa578664ca61a5d2a5f676e_9234593ba50142b62d7609a25fa9c6a5 | False→True | explicit_gold_display_unit_overridden_by_other_table | $29.6 billion | 29.6 |
| TAT-QA:fe0e8fe94bab06428abbca1372dc801f_3b1659ecae50b5da79d5ab902fea9447 | False→True | requested_cardinality_vs_threshold_financial_quantity | 2 | 2.0 |

测试：`tests/test_full_metric_repairs.py`与`tests/test_metrics.py`合计47项通过。覆盖单位优先级、输入/输出维度、币种与尺度冲突、年份判定、百分点输入及未知尺度拒绝；旧评分快照未改。
